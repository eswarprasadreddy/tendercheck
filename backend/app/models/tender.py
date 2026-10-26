from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.requirement import Requirement
    from app.models.vendor_document import VendorDocument
    from app.models.report import Report


class TenderStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    pdf_path: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=TenderStatus.UPLOADED.value, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )
    vendor_documents: Mapped[list["VendorDocument"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )
