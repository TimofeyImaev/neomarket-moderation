"""POST /api/v1/products/{product_id}/decline — MOD-04/05."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth import get_current_moderator_id
from src.database import get_db
from src.schemas.moderation import DeclineIn
from src.services.decline import decline_product

router = APIRouter()


@router.post("/products/{product_id}/decline", status_code=200)
def decline(
    product_id: str,
    body: DeclineIn,
    db: Session = Depends(get_db),
    moderator_id: str = Depends(get_current_moderator_id),
):
    return decline_product(db, product_id, body, moderator_id)
