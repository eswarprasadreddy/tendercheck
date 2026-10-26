"""
Report endpoints.

POST /api/v1/tenders/{tender_id}/vendors/{vendor_name}/report
    - Generates or updates an evaluation report aggregating matches and contradictions.

POST /report/confirm (and /api/v1/reports/confirm)
    - Officer confirmation endpoint: the ONLY way to finalize an evaluation report.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


from app.database import get_db
from app.models.contradiction import Contradiction
from app.models.match import Match
from app.models.report import Report
from app.models.requirement import Requirement
from app.models.tender import Tender
from app.models.vendor_document import VendorDocument
from app.schemas.contradiction import ContradictionResponse
from app.schemas.match import MatchResponse
from app.schemas.report import ReportConfirmRequest, ReportResponse
from app.services.report_service import confirm_report, generate_vendor_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


async def _enrich_report(db: AsyncSession, report: Report) -> ReportResponse:
    """Enrich report response with matches and contradictions."""
    req_ids = list(
        await db.scalars(
            select(Requirement.id).where(Requirement.tender_id == report.tender_id)
        )
    )
    matches: list[Match] = []
    if req_ids:
        v_doc_ids = list(
            await db.scalars(
                select(VendorDocument.id).where(
                    VendorDocument.tender_id == report.tender_id,
                    VendorDocument.vendor_name == report.vendor_name,
                )
            )
        )
        res = await db.scalars(
            select(Match)
            .options(selectinload(Match.requirement))
            .where(
                Match.requirement_id.in_(req_ids),
                (Match.vendor_document_id.in_(v_doc_ids)) | (Match.vendor_document_id.is_(None)),
            )
        )
        matches = list(res)

    c_res = await db.scalars(
        select(Contradiction).where(
            Contradiction.tender_id == report.tender_id,
            Contradiction.vendor_name == report.vendor_name,
        )
    )
    contradictions = list(c_res)

    resp = ReportResponse.model_validate(report)
    resp.matches = [MatchResponse.model_validate(m) for m in matches]
    resp.contradictions = [ContradictionResponse.model_validate(c) for c in contradictions]
    return resp


@router.post(
    "/tenders/{tender_id}/vendors/{vendor_name}/report",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate or recalculate an evaluation report for a vendor",
)
async def generate_report_endpoint(
    tender_id: uuid.UUID,
    vendor_name: str,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    tender = await db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found.")

    report = await generate_vendor_report(db=db, tender_id=tender_id, vendor_name=vendor_name)
    return await _enrich_report(db, report)


@router.get(
    "/tenders/{tender_id}/vendors/{vendor_name}/report",
    response_model=ReportResponse,
    summary="Get or generate an evaluation report for a vendor",
)
async def get_vendor_report_endpoint(
    tender_id: uuid.UUID,
    vendor_name: str,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await generate_vendor_report(db=db, tender_id=tender_id, vendor_name=vendor_name)
    return await _enrich_report(db, report)


@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
    summary="Get report by ID",
)
async def get_report_by_id(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return await _enrich_report(db, report)


@router.post(
    "/reports/confirm",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Officer confirmation: the only way to finalize an evaluation report",
)
@router.post(
    "/report/confirm",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Officer confirmation (direct path)",
)
async def confirm_report_endpoint(
    payload: ReportConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    if payload.report_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="report_id is required.",
        )

    try:
        confirmed = await confirm_report(
            db=db,
            report_id=payload.report_id,
            officer_id=payload.officer_id,
            officer_notes=payload.officer_notes,
            confirmed_verdict=payload.confirmed_verdict,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return await _enrich_report(db, confirmed)
