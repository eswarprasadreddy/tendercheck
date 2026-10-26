"""
Match model — one row per (requirement, vendor).

Evidence rules
--------------
PASS / FAIL / MISMATCH  →  evidence_file, evidence_page, evidence_quote are REQUIRED
MISSING                 →  searched_in (JSONB) is REQUIRED; evidence columns are null

Enforcement is at the Pydantic schema layer, not the DB layer (to keep the DB
simple and avoid complex CHECK constraints).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.requirement import Requirement
    from app.models.vendor_document import VendorDocument


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MISSING = "MISSING"
    MISMATCH = "MISMATCH"
    ERROR = "ERROR"


class CheckedBy(str, Enum):
    LLM = "llm"
    NUMERIC_ENGINE = "numeric_engine"
    DATE_ENGINE = "date_engine"
    SPEC_ENGINE = "spec_engine"
    OFFICER = "officer"
    SYSTEM = "system"




class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    vendor_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendor_documents.id", ondelete="SET NULL"),
        nullable=True  # null for MISSING
    )

    verdict: Mapped[str] = mapped_column(String(10), nullable=False)
    verdict_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Required for PASS / FAIL / MISMATCH
    evidence_file: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Parsed value extracted from vendor document (for numeric/spec comparison display)
    extracted_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Required for MISSING — lists docs searched and terms used
    # e.g. {"documents": ["turnover_cert.pdf"], "terms": ["turnover", "revenue"]}
    searched_in: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    checked_by: Mapped[str] = mapped_column(String(20), nullable=False)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    requirement: Mapped["Requirement"] = relationship(back_populates="matches")
    vendor_document: Mapped[Optional["VendorDocument"]] = relationship(
        back_populates="matches"
    )
