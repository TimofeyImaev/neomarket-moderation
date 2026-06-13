"""GET /api/v1/product-blocking-reasons."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth import get_current_moderator_id
from src.database import get_db
from src.models.moderation import ProductBlockingReason

router = APIRouter()


@router.get("/product-blocking-reasons", status_code=200)
def list_reasons(
    db: Session = Depends(get_db),
    _: str = Depends(get_current_moderator_id),
):
    reasons = db.query(ProductBlockingReason).order_by(ProductBlockingReason.title).all()
    return [
        {"id": r.id, "title": r.title, "hard_block": r.hard_block}
        for r in reasons
    ]
