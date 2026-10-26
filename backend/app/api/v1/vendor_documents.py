"""
Vendor Document endpoints.

POST /api/v1/tenders/{tender_id}/vendors/upload
    - Upload vendor PDF document
    - Extract text per-page using PyMuPDF / OCR (same pipeline as tender)
    - Store file and metadata
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tender import Tender
from app.models.vendor_document import VendorDocument
from app.schemas.vendor_document import VendorDocumentResponse
from app.services.vendor_service import save_and_extract_vendor_document

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vendor-documents"])


async def _handle_upload(
    file: UploadFile,
    tender_id: uuid.UUID,
    vendor_name: str,
    doc_type: Optional[str],
    db: AsyncSession,
) -> VendorDocumentResponse:
    # Validate tender exists
    tender = await db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender {tender_id} not found.")

    # Validate PDF extension
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted for vendor documents.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    doc = await save_and_extract_vendor_document(
        db=db,
        tender_id=tender_id,
        vendor_name=vendor_name,
        original_filename=file.filename or "vendor_document.pdf",
        content=content,
        doc_type=doc_type,
    )

    return VendorDocumentResponse.model_validate(doc)


@router.post(
    "/tenders/{tender_id}/vendors/upload",
    response_model=VendorDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a vendor PDF document and run per-page text extraction",
)
async def upload_vendor_document(
    tender_id: uuid.UUID,
    file: UploadFile,
    vendor_name: str = Form(..., description="Vendor / Bidder company name"),
    doc_type: Optional[str] = Form(None, description="e.g. balance_sheet, gst_certificate, specs"),
    db: AsyncSession = Depends(get_db),
) -> VendorDocumentResponse:
    return await _handle_upload(
        file=file,
        tender_id=tender_id,
        vendor_name=vendor_name,
        doc_type=doc_type,
        db=db,
    )


@router.post(
    "/vendor-documents/upload",
    response_model=VendorDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a vendor PDF document (alternative path)",
)
async def upload_vendor_document_alt(
    file: UploadFile,
    tender_id: uuid.UUID = Form(...),
    vendor_name: str = Form(..., description="Vendor / Bidder company name"),
    doc_type: Optional[str] = Form(None, description="e.g. balance_sheet, gst_certificate, specs"),
    db: AsyncSession = Depends(get_db),
) -> VendorDocumentResponse:
    return await _handle_upload(
        file=file,
        tender_id=tender_id,
        vendor_name=vendor_name,
        doc_type=doc_type,
        db=db,
    )



@router.get(
    "/tenders/{tender_id}/vendors",
    summary="List all unique vendors with uploaded documents for a tender",
)
async def list_vendors_for_tender(
    tender_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    docs = await db.scalars(
        select(VendorDocument).where(VendorDocument.tender_id == tender_id)
    )
    all_docs = list(docs)
    vendor_map: dict[str, dict] = {}
    for d in all_docs:
        name = d.vendor_name
        if name not in vendor_map:
            vendor_map[name] = {
                "vendor_name": name,
                "document_count": 0,
                "documents": [],
            }
        vendor_map[name]["document_count"] += 1
        vendor_map[name]["documents"].append({
            "id": str(d.id),
            "filename": d.original_filename,
            "doc_type": d.doc_type,
            "page_count": d.page_count,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return list(vendor_map.values())


@router.get(
    "/tenders/{tender_id}/vendors/{vendor_name}/documents",
    response_model=list[VendorDocumentResponse],
    summary="List all uploaded documents for a vendor under a tender",
)
async def list_vendor_documents(
    tender_id: uuid.UUID,
    vendor_name: str,
    db: AsyncSession = Depends(get_db),
) -> list[VendorDocumentResponse]:
    docs = await db.scalars(
        select(VendorDocument).where(
            VendorDocument.tender_id == tender_id,
            VendorDocument.vendor_name == vendor_name,
        )
    )
    return [VendorDocumentResponse.model_validate(d) for d in docs]

