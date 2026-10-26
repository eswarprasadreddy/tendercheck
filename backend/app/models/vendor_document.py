from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tender import Tender
    from app.models.match import Match


class VendorDocStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class VendorDocument(Base):
    __tablename__ = "vendor_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # e.g. "balance_sheet", "gst_certificate", "oem_authorization", "experience_cert"
    doc_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=VendorDocStatus.UPLOADED.value, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tender: Mapped["Tender"] = relationship(back_populates="vendor_documents")
    matches: Mapped[list["Match"]] = relationship(
        back_populates="vendor_document", cascade="all, delete-orphan"
    )
