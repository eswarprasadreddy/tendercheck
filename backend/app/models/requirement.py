"""
Requirement model — sector-agnostic by design.

``requirement_type`` drives which checker handles verification:
  - numeric / date  →  Python engine (never the LLM)
  - spec            →  Python engine for numeric specs; LLM for text specs
  - boolean / text / certification / classification  →  LLM evidence matcher

Adding a new sector never requires changing this enum — just add a sector JSON
config under app/sectors/<sector_id>.json.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tender import Tender
    from app.models.match import Match


class RequirementType(str, Enum):
    """
    Sector-agnostic requirement type enum.

    IT-hardware mapping examples
    ----------------------------
    numeric        → min turnover, experience years, similar order count, warranty yrs
    date           → certificate validity, bid validity date
    boolean        → GST present, OEM auth letter present
    spec           → RAM ≥ 16 GB, SSD ≥ 512 GB, display ≥ 15.6 in
    certification  → ISO 9001, BIS, MSME (bool + optional validity date)
    classification → Make in India class (Class I / II / III)
    text           → allowed values / pattern (e.g. country of origin = "India")
    """

    NUMERIC = "numeric"
    DATE = "date"
    BOOLEAN = "boolean"
    SPEC = "spec"
    CERTIFICATION = "certification"
    CLASSIFICATION = "classification"
    TEXT = "text"


class RequirementCategory(str, Enum):
    """High-level grouping used for report sections and UI filtering."""

    FINANCIAL = "financial"            # turnover, net worth, similar order value
    EXPERIENCE = "experience"          # years in business, past order count
    LEGAL = "legal"                    # GST, company registration
    CERTIFICATION = "certification"    # ISO, BIS, OEM auth, MSME, Startup cert
    TECHNICAL_SPEC = "technical_spec"  # RAM, SSD, processor, display, battery
    DELIVERY = "delivery"              # warranty period, delivery timeline
    COMPLIANCE = "compliance"          # Make in India class, local content %
    OTHER = "other"


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Core fields
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Comparison semantics — null for boolean / text types
    operator: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Structured value payload; shape depends on requirement_type (see schemas)
    value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Convenience flat columns (denormalised from value for SQL queries)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Provenance
    source_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_quote: Mapped[str] = mapped_column(Text, nullable=False)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Sector-config field key (e.g. "ram_gb", "iso_9001", "annual_turnover")
    # Lets the numeric/spec checker know the canonical field name
    sector_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tender: Mapped["Tender"] = relationship(back_populates="requirements")
    matches: Mapped[list["Match"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )
