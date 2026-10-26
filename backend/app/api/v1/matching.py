"""
Matching Engine endpoints.

POST /api/v1/tenders/{tender_id}/vendors/{vendor_name}/match
    - Runs matching engine: evidence extraction via Gemini + plain Python verification.
    - Persists matches following evidence rules.
    - Runs cross-document contradiction detection.

GET /api/v1/tenders/{tender_id}/vendors/{vendor_name}/matches
    - Lists all matches for the vendor.

GET /api/v1/tenders/{tender_id}/vendors/{vendor_name}/contradictions
    - Lists all detected contradictions for the vendor.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contradiction import Contradiction
from app.models.match import Match
from app.models.requirement import Requirement
from app.models.tender import Tender
from app.models.vendor_document import VendorDocument
from app.schemas.contradiction import ContradictionResponse
from app.schemas.match import MatchResponse, MatchVerdictUpdate
from app.services.matching_engine import MatchingEngine
from app.services.report_service import generate_vendor_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["matching"])



@router.post(
    "/tenders/{tender_id}/vendors/{vendor_name}/match",
    response_model=list[MatchResponse],
    status_code=status.HTTP_200_OK,
    summary="Run matching engine against vendor documents",
)
async def run_matching_endpoint(
    tender_id: uuid.UUID,
    vendor_name: str,
    db: AsyncSession = Depends(get_db),
) -> list[MatchResponse]:
    tender = await db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found.")

    engine = MatchingEngine()
    matches = await engine.run_matching(db=db, tender_id=tender_id, vendor_name=vendor_name)
    await generate_vendor_report(db=db, tender_id=tender_id, vendor_name=vendor_name)

    match_ids = [m.id for m in matches]
    loaded_matches: list[Match] = []
    if match_ids:
        res = await db.scalars(
            select(Match)
            .options(selectinload(Match.requirement))
            .where(Match.id.in_(match_ids))
        )
        loaded_matches = list(res)
    return [MatchResponse.model_validate(m) for m in loaded_matches]


@router.get(
    "/tenders/{tender_id}/vendors/{vendor_name}/matches",
    response_model=list[MatchResponse],
    summary="List matches for a vendor under a tender",
)
async def list_matches(
    tender_id: uuid.UUID,
    vendor_name: str,
    db: AsyncSession = Depends(get_db),
) -> list[MatchResponse]:
    req_ids = list(
        await db.scalars(
            select(Requirement.id).where(Requirement.tender_id == tender_id)
        )
    )
    if not req_ids:
        return []

    # Get vendor document IDs for this vendor
    v_doc_ids = list(
        await db.scalars(
            select(VendorDocument.id).where(
                VendorDocument.tender_id == tender_id,
                VendorDocument.vendor_name == vendor_name,
            )
        )
    )

    matches = await db.scalars(
        select(Match)
        .options(selectinload(Match.requirement))
        .where(
            Match.requirement_id.in_(req_ids),
            (Match.vendor_document_id.in_(v_doc_ids)) | (Match.vendor_document_id.is_(None)),
        )
    )
    return [MatchResponse.model_validate(m) for m in matches]


@router.get(
    "/tenders/{tender_id}/vendors/{vendor_name}/contradictions",
    response_model=list[ContradictionResponse],
    summary="List contradictions detected across vendor documents",
)
async def list_contradictions(
    tender_id: uuid.UUID,
    vendor_name: str,
    db: AsyncSession = Depends(get_db),
) -> list[ContradictionResponse]:
    rows = await db.scalars(
        select(Contradiction).where(
            Contradiction.tender_id == tender_id,
            Contradiction.vendor_name == vendor_name,
        )
    )
    return [ContradictionResponse.model_validate(c) for c in rows]


@router.patch(
    "/matches/{match_id}",
    response_model=MatchResponse,
    summary="Officer review: approve or override each verdict with an officer note",
)
async def update_match_verdict(
    match_id: uuid.UUID,
    payload: MatchVerdictUpdate,
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    match = await db.get(Match, match_id, options=[selectinload(Match.requirement)])
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    old_verdict = match.verdict
    match.verdict = payload.verdict.value
    match.checked_by = "officer"

    note_text = payload.officer_notes.strip() if payload.officer_notes else ""
    if match.verdict != old_verdict:
        match.verdict_reason = f"Officer overridden from {old_verdict} to {match.verdict}." + (f" Note: {note_text}" if note_text else "")
    elif note_text:
        match.verdict_reason = f"{match.verdict_reason} [Officer: {note_text}]"

    # Enforce schema validity for the verdict
    if match.verdict in ("PASS", "FAIL", "MISMATCH"):
        if not match.evidence_file:
            match.evidence_file = "Officer Bid Review / Manual Verification"
        if match.evidence_page is None:
            match.evidence_page = 1
        if not match.evidence_quote:
            match.evidence_quote = note_text or "Confirmed and validated directly by Officer during evaluation review."
    elif match.verdict == "MISSING":
        if not match.searched_in:
            match.searched_in = {"documents": ["bid_submission_documents"], "terms": ["officer_checked"]}

    await db.commit()
    await db.refresh(match, attribute_names=["requirement"])

    # If requirement exists, recalculate vendor report
    if match.requirement:
        tender_id = match.requirement.tender_id
        # Find vendor name
        vendor_name = None
        if match.vendor_document_id:
            v_doc = await db.get(VendorDocument, match.vendor_document_id)
            if v_doc:
                vendor_name = v_doc.vendor_name
        if not vendor_name:
            # Check report for this tender
            reps = list(await db.scalars(select(Report).where(Report.tender_id == tender_id)))
            if reps:
                vendor_name = reps[0].vendor_name
        if vendor_name:
            await generate_vendor_report(db=db, tender_id=tender_id, vendor_name=vendor_name)

    return MatchResponse.model_validate(match)

