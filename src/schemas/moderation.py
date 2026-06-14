from pydantic import BaseModel, ConfigDict


# --- Incoming events from B2B (internal format, used directly in tests) ---

class B2BProductEventIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: str
    seller_id: str
    event: str  # CREATED | EDITED | DELETED
    date: str


# --- Incoming events from B2B (OpenAPI format for /b2b/events endpoint) ---

class IncomingB2BEventHTTP(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_type: str        # PRODUCT_CREATED | PRODUCT_EDITED | PRODUCT_DELETED
    idempotency_key: str
    occurred_at: str
    payload: dict


# --- Approve ---

class ApproveIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    moderator_comment: str | None = None


# --- Decline (soft + hard block) ---

class FieldReportIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    field_name: str
    sku_id: str | None = None
    comment: str


class DeclineIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    blocking_reason_ids: list[str]   # minItems: 1 - use first
    moderator_comment: str
    field_reports: list[FieldReportIn] = []
