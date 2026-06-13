"""POST /api/v1/events/product — входящие события от B2B."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth import verify_b2b_service_key
from src.database import get_db
from src.schemas.moderation import B2BProductEventIn
from src.services.events import handle_b2b_event

router = APIRouter()


@router.post("/events/product", status_code=200)
def receive_product_event(
    body: B2BProductEventIn,
    db: Session = Depends(get_db),
    _=Depends(verify_b2b_service_key),
):
    handle_b2b_event(db, body)
    return {"status": "ok"}
