"""Обработка входящих событий от B2B (MOD-1)."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.errors import ApiError
from src.models.moderation import ProductModeration
from src.schemas.moderation import B2BProductEventIn
from src.services.b2b_client import fetch_product_json


def _compute_priority(old_status: str, total_active_qty: int) -> int:
    if old_status == "BLOCKED":
        return 2
    if old_status == "MODERATED" and total_active_qty > 0:
        return 3
    if old_status == "MODERATED" and total_active_qty == 0:
        return 4
    return 1  # PENDING/IN_REVIEW — оставляем как есть (не меняем)


def _total_active_qty(json_after: dict) -> int:
    return sum(s.get("active_quantity", 0) for s in json_after.get("skus", []))


def handle_b2b_event(db: Session, data: B2BProductEventIn, product_json: dict | None = None) -> None:
    card = db.query(ProductModeration).filter_by(product_id=data.product_id).first()

    if data.event == "CREATED":
        if card is not None:
            if card.status == "HARD_BLOCKED":
                return  # игнорируем
            raise ApiError(400, "INVALID_REQUEST", "Duplicate CREATED event for this product")

        json_after = product_json or fetch_product_json(data.product_id) or {}
        db.add(ProductModeration(
            product_id=data.product_id,
            seller_id=data.seller_id,
            status="PENDING",
            queue_priority=1,
            json_before=None,
            json_after=json_after,
        ))
        db.commit()

    elif data.event == "EDITED":
        if card is None:
            raise ApiError(400, "INVALID_REQUEST", "EDITED event for unknown product")
        if card.status == "HARD_BLOCKED":
            return  # игнорируем

        old_status = card.status
        json_after = product_json or fetch_product_json(data.product_id) or card.json_after

        # Определяем приоритет
        if old_status in ("PENDING", "IN_REVIEW"):
            new_priority = card.queue_priority  # сохраняем
        else:
            new_priority = _compute_priority(old_status, _total_active_qty(json_after))

        card.json_before = card.json_after
        card.json_after = json_after
        card.status = "PENDING"
        card.queue_priority = new_priority
        card.moderator_id = None
        card.date_updated = datetime.now(timezone.utc)
        # Очищаем field_reports
        for fr in list(card.field_reports):
            db.delete(fr)
        db.commit()

    elif data.event == "DELETED":
        if card is None:
            return  # идемпотентно
        db.delete(card)
        db.commit()

    else:
        raise ApiError(400, "INVALID_REQUEST", f"Unknown event type: {data.event}")
