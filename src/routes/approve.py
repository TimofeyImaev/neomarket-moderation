"""POST /api/v1/tickets/{ticket_id}/approve — MOD-03."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth import get_current_moderator_id
from src.database import get_db
from src.schemas.moderation import ApproveIn
from src.services.approve import approve_product

router = APIRouter()


@router.post("/tickets/{ticket_id}/approve", status_code=200)
def approve(
    ticket_id: str,
    body: ApproveIn,
    db: Session = Depends(get_db),
    moderator_id: str = Depends(get_current_moderator_id),
):
    return approve_product(db, ticket_id, body, moderator_id)
