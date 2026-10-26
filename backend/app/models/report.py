from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tender import Tender


class OverallVerdict(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    UNDER_REVIEW = "UNDER_REVIEW"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    overall_verdict: Mapped[str] = mapped_column(
        String(20), default=OverallVerdict.UNDER_REVIEW.value, nullable=False
    )

    # Counts
    pass_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fail_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mismatch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contradiction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Human review gate — AI is advisory only; officer must confirm final verdict
    officer_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    officer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    officer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tender: Mapped["Tender"] = relationship(back_populates="reports")
