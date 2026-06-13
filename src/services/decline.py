"""MOD-04/05: Отклонить карточку (мягкая / жёсткая блокировка)."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.errors import ApiError
from src.models.moderation import ProductBlockingReason, ProductModeration, ProductModerationFieldReport
from src.schemas.moderation import DeclineIn
from src.services.b2b_client import send_moderation_decision


def decline_product(db: Session, product_id: str, data: DeclineIn, moderator_id: str) -> dict:
    q = db.query(ProductModeration).filter_by(product_id=product_id)
    if db.bind.dialect.name != "sqlite":
        q = q.with_for_update()
    card = q.first()

    if card is None:
        raise ApiError(404, "NOT_FOUND", "Moderation card not found")

    if card.moderator_id is not None and card.moderator_id != moderator_id:
        raise ApiError(403, "FORBIDDEN", "This card is assigned to another moderator")

    if card.status in ("MODERATED", "BLOCKED", "HARD_BLOCKED"):
        raise ApiError(409, "INVALID_STATUS", f"Cannot decline card in status {card.status}")

    reason = db.get(ProductBlockingReason, data.blocking_reason_id)
    if reason is None:
        raise ApiError(404, "NOT_FOUND", "Blocking reason not found")

    is_hard = reason.hard_block
    new_status = "HARD_BLOCKED" if is_hard else "BLOCKED"

    card.status = new_status
    card.moderator_id = moderator_id
    card.moderator_comment = data.moderator_comment
    card.blocking_reason_id = data.blocking_reason_id
    card.date_moderation = datetime.now(timezone.utc)
    card.date_updated = datetime.now(timezone.utc)

    for fr in list(card.field_reports):
        db.delete(fr)
    db.flush()

    for fr_in in data.field_reports:
        db.add(ProductModerationFieldReport(
            product_moderation_id=card.id,
            field_name=fr_in.field_name,
            sku_id=fr_in.sku_id,
            comment=fr_in.comment,
        ))

    db.commit()
    db.refresh(card)

    payload = {
        "idempotency_key": card.id,
        "product_id": product_id,
        "status": "BLOCKED",
        "hard_block": is_hard,
        "blocking_reason": {
            "id": reason.id,
            "title": reason.title,
            "comment": data.moderator_comment,
        },
        "field_reports": [
            {"field_name": fr.field_name, "sku_id": fr.sku_id, "comment": fr.comment}
            for fr in card.field_reports
        ],
    }
    send_moderation_decision(product_id, payload)

    return {"status": "ok", "product_id": product_id}
