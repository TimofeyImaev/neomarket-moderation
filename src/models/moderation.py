import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductBlockingReason(Base):
    __tablename__ = "product_blocking_reasons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    hard_block: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cards: Mapped[list["ProductModeration"]] = relationship(back_populates="blocking_reason")


class ProductModeration(Base):
    __tablename__ = "product_moderation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    seller_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    queue_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    json_before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    json_after: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    blocking_reason_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("product_blocking_reasons.id"), nullable=True
    )
    moderator_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    moderator_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    date_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
    date_moderation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    blocking_reason: Mapped["ProductBlockingReason | None"] = relationship(back_populates="cards")
    field_reports: Mapped[list["ProductModerationFieldReport"]] = relationship(
        back_populates="card", cascade="all, delete-orphan"
    )


class ProductModerationFieldReport(Base):
    __tablename__ = "product_moderation_field_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    product_moderation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("product_moderation.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sku_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    card: Mapped[ProductModeration] = relationship(back_populates="field_reports")
