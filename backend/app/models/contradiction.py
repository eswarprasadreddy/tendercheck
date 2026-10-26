"""
Contradiction model — records cross-document field mismatches for a vendor.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Contradiction(Base):
    __tablename__ = "contradictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # e.g. "employee_count", "annual_turnover"
    field: Mapped[str] = mapped_column(String(100), nullable=False)

    doc_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    doc_a_filename: Mapped[str] = mapped_column(Text, nullable=False)
    doc_a_value: Mapped[str] = mapped_column(Text, nullable=False)

    doc_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    doc_b_filename: Mapped[str] = mapped_column(Text, nullable=False)
    doc_b_value: Mapped[str] = mapped_column(Text, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
