"""MOD-03: Одобрить карточку модерации."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.errors import ApiError
from src.models.moderation import ProductModeration
from src.schemas.moderation import ApproveIn
from src.services.b2b_client import send_moderation_decision


def approve_product(db: Session, ticket_id: str, data: ApproveIn, moderator_id: str) -> dict:
    q = db.query(ProductModeration).filter_by(id=ticket_id)
    if db.bind.dialect.name != "sqlite":
        q = q.with_for_update()
    card = q.first()

    if card is None:
        raise ApiError(404, "NOT_FOUND", "Moderation card not found")

    # Spec: approve declares only 200/409 (moderation/openapi.yaml:343-349).
    # A foreign ticket is "Чужой тикет" → 409, NOT 403.
    if card.moderator_id is not None and card.moderator_id != moderator_id:
        raise ApiError(409, "FOREIGN_TICKET", "This card is assigned to another moderator")

    # Only IN_REVIEW tickets may be approved — any other status, including the
    # terminal HARD_BLOCKED, is "Неверный статус" → 409 (never 403).
    if card.status != "IN_REVIEW":
        raise ApiError(409, "INVALID_STATUS", f"Cannot approve card in status {card.status}")

    skus = card.json_after.get("skus", [])
    if not skus:
        raise ApiError(409, "NO_SKU", "Cannot approve product without SKUs")

    card.status = "APPROVED"          # TicketStatus enum: APPROVED per moderation/openapi.yaml:651-653
    card.moderator_id = moderator_id
    card.moderator_comment = data.comment   # store in DB column; schema field renamed to comment
    card.date_moderation = datetime.now(timezone.utc)
    card.date_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(card)

    payload = {
        "idempotency_key": card.id,
        "product_id": card.product_id,
        "event_type": "MODERATED",    # B2B event type stays MODERATED
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    send_moderation_decision(card.product_id, payload)

    # Return TicketResponse per moderation/openapi.yaml:343
    return {
        "id": card.id,
        "product_id": card.product_id,
        "seller_id": card.seller_id,
        "kind": "CREATE" if card.json_before is None else "EDIT",
        "status": card.status,
        "queue_priority": card.queue_priority,
        "created_at": card.date_created.isoformat() if card.date_created else None,
    }
