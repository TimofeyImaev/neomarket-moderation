"""POST /api/v1/products/{product_id}/approve — MOD-03."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth import get_current_moderator_id
from src.database import get_db
from src.schemas.moderation import ApproveIn
from src.services.approve import approve_product

router = APIRouter()


@router.post("/products/{product_id}/approve", status_code=200)
def approve(
    product_id: str,
    body: ApproveIn,
    db: Session = Depends(get_db),
    moderator_id: str = Depends(get_current_moderator_id),
):
    return approve_product(db, product_id, body, moderator_id)
