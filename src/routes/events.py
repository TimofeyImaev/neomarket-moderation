"""POST /api/v1/b2b/events - incoming events from B2B."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth import verify_b2b_service_key
from src.database import get_db
from src.schemas.moderation import B2BProductEventIn, IncomingB2BEventHTTP
from src.services.events import handle_b2b_event

router = APIRouter()

_EVENT_TYPE_MAP = {
    "PRODUCT_CREATED": "CREATED",
    "PRODUCT_EDITED": "EDITED",
    "PRODUCT_DELETED": "DELETED",
}


@router.post("/b2b/events", status_code=202)
def receive_b2b_event(
    body: IncomingB2BEventHTTP,
    db: Session = Depends(get_db),
    _=Depends(verify_b2b_service_key),
):
    payload = body.payload or {}
    internal = B2BProductEventIn(
        product_id=payload.get("product_id", ""),
        seller_id=payload.get("seller_id", ""),
        event=_EVENT_TYPE_MAP.get(body.event_type, body.event_type),
        date=body.occurred_at,
    )
    json_after = payload.get("json_after") or payload.get("json_before")
    handle_b2b_event(db, internal, product_json=json_after)
    return {"status": "ok"}
