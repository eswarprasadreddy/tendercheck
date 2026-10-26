"""
Vendor document service.

Handles:
1. Vendor document upload and storage.
2. Per-page text extraction via the same pipeline as tender (`extract_pdf`).
3. Updating vendor document status and storing extracted text.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor_document import VendorDocStatus, VendorDocument
from app.services.file_storage import save_upload, vendor_dir
from app.services.pdf_extractor import extract_pdf

logger = logging.getLogger(__name__)


def process_vendor_document_sync(
    doc_id: uuid.UUID,
    pdf_path: Path,
) -> tuple[str, int, str]:
    """
    Synchronously extracts text and page count from a vendor document PDF.
    Returns (raw_text, page_count, status).
    """
    try:
        result = extract_pdf(pdf_path)
        return result.full_text, result.page_count, VendorDocStatus.READY.value
    except Exception as exc:
        logger.exception("Failed to extract vendor document %s: %s", doc_id, exc)
        return "", 0, VendorDocStatus.FAILED.value


async def save_and_extract_vendor_document(
    db: AsyncSession,
    tender_id: uuid.UUID,
    vendor_name: str,
    original_filename: str,
    content: bytes,
    doc_type: Optional[str] = None,
) -> VendorDocument:
    """
    Create a VendorDocument record, write the file to disk, and extract text per-page.
    """
    # Create DB record with status UPLOADED
    vendor_doc = VendorDocument(
        tender_id=tender_id,
        vendor_name=vendor_name,
        doc_type=doc_type,
        original_filename=original_filename,
        pdf_path="pending",
        status=VendorDocStatus.PROCESSING.value,
    )
    db.add(vendor_doc)
    await db.flush()

    # Save to disk
    v_dir = vendor_dir(tender_id, vendor_name)
    safe_filename = f"{vendor_doc.id}_{original_filename}"
    dest_path = v_dir / safe_filename
    await save_upload(dest_path, content)
    vendor_doc.pdf_path = str(dest_path)

    # Extract text using same pipeline as tender
    try:
        result = extract_pdf(dest_path)
        vendor_doc.raw_text = result.full_text
        vendor_doc.page_count = result.page_count
        vendor_doc.status = VendorDocStatus.READY.value
    except Exception as exc:
        logger.exception("Text extraction failed for %s: %s", original_filename, exc)
        vendor_doc.status = VendorDocStatus.FAILED.value
        vendor_doc.error_message = str(exc)

    await db.commit()
    await db.refresh(vendor_doc)
    return vendor_doc
