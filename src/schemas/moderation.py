from pydantic import BaseModel, ConfigDict


# ── Входящие события от B2B ──────────────────────────────────────────────────

class B2BProductEventIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: str
    seller_id: str
    event: str  # CREATED | EDITED | DELETED
    date: str


# ── Approve ──────────────────────────────────────────────────────────────────

class ApproveIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    moderator_comment: str | None = None


# ── Decline (soft + hard block) ───────────────────────────────────────────────

class FieldReportIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    field_name: str
    sku_id: str | None = None
    comment: str


class DeclineIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    blocking_reason_id: str
    moderator_comment: str
    field_reports: list[FieldReportIn] = []
