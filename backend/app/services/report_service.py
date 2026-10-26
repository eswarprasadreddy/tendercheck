"""
Report service.

Handles:
1. Compiling and generating evaluation reports aggregating matches and contradictions.
2. Confirming and finalizing reports via officer sign-off.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contradiction import Contradiction
from app.models.match import Match, Verdict
from app.models.report import OverallVerdict, Report
from app.models.requirement import Requirement
from app.models.vendor_document import VendorDocument

logger = logging.getLogger(__name__)


async def generate_vendor_report(
    db: AsyncSession,
    tender_id: uuid.UUID,
    vendor_name: str,
) -> Report:
    """
    Generate or recalculate an evaluation report for a vendor against a tender.
    Aggregates match verdicts and contradictions.
    """
    # 1. Fetch requirements for tender
    req_ids = list(
        await db.scalars(
            select(Requirement.id).where(Requirement.tender_id == tender_id)
        )
    )

    # 2. Fetch matches for this vendor
    v_docs = list(
        await db.scalars(
            select(VendorDocument).where(
                VendorDocument.tender_id == tender_id,
                VendorDocument.vendor_name == vendor_name,
            )
        )
    )
    v_doc_ids = {d.id for d in v_docs}
    v_doc_names = {d.original_filename for d in v_docs}

    matches: list[Match] = []
    if req_ids:
        all_res = await db.scalars(
            select(Match).where(Match.requirement_id.in_(req_ids))
        )
        for m in all_res:
            if not v_docs:
                matches.append(m)
            elif m.vendor_document_id in v_doc_ids:
                matches.append(m)
            elif m.vendor_document_id is None:
                if not m.searched_in or not m.searched_in.get("documents"):
                    matches.append(m)
                else:
                    docs_searched = set(m.searched_in.get("documents", []))
                    if docs_searched.intersection(v_doc_names):
                        matches.append(m)

    # 3. Fetch contradictions
    c_res = await db.scalars(
        select(Contradiction).where(
            Contradiction.tender_id == tender_id,
            Contradiction.vendor_name == vendor_name,
        )
    )
    contradictions = list(c_res)

    # 4. Compute counts
    pass_count = sum(1 for m in matches if m.verdict == Verdict.PASS.value)
    fail_count = sum(1 for m in matches if m.verdict == Verdict.FAIL.value)
    missing_count = sum(1 for m in matches if m.verdict == Verdict.MISSING.value)
    mismatch_count = sum(1 for m in matches if m.verdict == Verdict.MISMATCH.value)
    error_count = sum(1 for m in matches if m.verdict == Verdict.ERROR.value)
    contradiction_count = len(contradictions)

    # 5. Advisory verdict (AI recommendation only — human confirms)
    if error_count > 0:
        overall_verdict = OverallVerdict.UNDER_REVIEW.value
    elif fail_count > 0 or missing_count > 0 or mismatch_count > 0 or contradiction_count > 0:
        overall_verdict = OverallVerdict.NON_COMPLIANT.value
    elif pass_count > 0:
        overall_verdict = OverallVerdict.COMPLIANT.value
    else:
        overall_verdict = OverallVerdict.UNDER_REVIEW.value


    # Check for existing report
    existing = await db.scalar(
        select(Report).where(
            Report.tender_id == tender_id,
            Report.vendor_name == vendor_name,
        )
    )

    if existing:
        report = existing
        # Only update counts and verdict if not already finalized by officer
        if not report.officer_confirmed:
            report.overall_verdict = overall_verdict
        report.pass_count = pass_count
        report.fail_count = fail_count
        report.missing_count = missing_count
        report.mismatch_count = mismatch_count
        report.contradiction_count = contradiction_count
    else:
        report = Report(
            tender_id=tender_id,
            vendor_name=vendor_name,
            overall_verdict=overall_verdict,
            pass_count=pass_count,
            fail_count=fail_count,
            missing_count=missing_count,
            mismatch_count=mismatch_count,
            contradiction_count=contradiction_count,
            officer_confirmed=False,
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)
    return report


async def confirm_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    officer_id: str,
    officer_notes: Optional[str] = None,
    confirmed_verdict: Optional[OverallVerdict] = None,
) -> Report:
    """
    Finalize an evaluation report.
    This is the ONLY way a report can be finalized (officer_confirmed=True).
    """
    report = await db.get(Report, report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found.")

    report.officer_confirmed = True
    report.officer_id = officer_id
    report.officer_notes = officer_notes
    report.confirmed_at = datetime.now(timezone.utc)

    if confirmed_verdict is not None:
        report.overall_verdict = confirmed_verdict.value

    await db.commit()
    await db.refresh(report)
    return report
