"""MOD-03: Одобрить карточку модерации."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.errors import ApiError
from src.models.moderation import ProductModeration
from src.schemas.moderation import ApproveIn
from src.services.b2b_client import send_moderation_decision


def approve_product(db: Session, product_id: str, data: ApproveIn, moderator_id: str) -> dict:
    q = db.query(ProductModeration).filter_by(product_id=product_id)
    if db.bind.dialect.name != "sqlite":
        q = q.with_for_update()
    card = q.first()

    if card is None:
        raise ApiError(404, "NOT_FOUND", "Moderation card not found")

    if card.moderator_id is not None and card.moderator_id != moderator_id:
        raise ApiError(403, "FORBIDDEN", "This card is assigned to another moderator")

    if card.status in ("MODERATED", "BLOCKED", "HARD_BLOCKED"):
        raise ApiError(409, "INVALID_STATUS", f"Cannot approve card in status {card.status}")

    skus = card.json_after.get("skus", [])
    if not skus:
        raise ApiError(409, "NO_SKU", "Cannot approve product without SKUs")

    card.status = "MODERATED"
    card.moderator_id = moderator_id
    card.moderator_comment = data.moderator_comment
    card.date_moderation = datetime.now(timezone.utc)
    card.date_updated = datetime.now(timezone.utc)
    db.commit()

    payload = {
        "idempotency_key": card.id,
        "product_id": product_id,
        "status": "MODERATED",
    }
    send_moderation_decision(product_id, payload)

    return {"status": "ok", "product_id": product_id}
