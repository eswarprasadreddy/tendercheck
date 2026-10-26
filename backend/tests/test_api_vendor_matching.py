"""
Integration tests for Vendor Document Upload, Matching Engine, and Report API routes.
"""
import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fpdf import FPDF

from app.models.match import CheckedBy, Verdict
from app.models.requirement import Requirement, RequirementCategory, RequirementType
from app.models.tender import Tender, TenderStatus
from app.models.vendor_document import VendorDocument


def _make_dummy_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, text, ln=True)
    return pdf.output()


@pytest.mark.asyncio
async def test_vendor_document_upload_api(async_client: AsyncClient, db_session: AsyncSession):
    """
    Test 1: Vendor documents upload with per-page text extraction (same pipeline as tender).
    """
    tender = Tender(
        title="Server Procurement",
        reference_number="GEM/2026/B/VEND-UP",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.commit()

    pdf_bytes = _make_dummy_pdf("Page 1: Annual turnover INR 2.50 Crore. OEM ISO 9001:2015 certified.")

    response = await async_client.post(
        f"/api/v1/tenders/{tender.id}/vendors/upload",
        data={"vendor_name": "TestVendor Corp", "doc_type": "technical_bid"},
        files={"file": ("test_doc.pdf", io.BytesIO(bytes(pdf_bytes)), "application/pdf")},
    )

    assert response.status_code == 201, f"Failed: {response.status_code} {response.text}"
    data = response.json()
    assert data["vendor_name"] == "TestVendor Corp"
    assert data["original_filename"] == "test_doc.pdf"
    assert data["status"] == "ready"
    assert data["page_count"] == 1


@pytest.mark.asyncio
async def test_report_generation_and_confirm_endpoints(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Test 2: Report generation endpoint and POST /report/confirm endpoint.
    """
    tender = Tender(
        title="IT Infrastructure 2026",
        reference_number="GEM/2026/B/REP-TEST",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.flush()

    req = Requirement(
        tender_id=tender.id,
        category=RequirementCategory.FINANCIAL.value,
        description="Turnover >= 1.5 Crore",
        requirement_type=RequirementType.NUMERIC.value,
        operator=">=",
        value={"amount": 15000000.0, "unit": "INR"},
        unit="INR",
        source_page=1,
        source_quote="Turnover must be at least 1.5 Crore.",
        is_mandatory=True,
    )
    db_session.add(req)
    await db_session.commit()

    # 1. Generate Report
    rep_res = await async_client.post(
        f"/api/v1/tenders/{tender.id}/vendors/AlphaTech/report"
    )
    assert rep_res.status_code == 200
    report_data = rep_res.json()
    assert report_data["vendor_name"] == "AlphaTech"
    assert report_data["officer_confirmed"] is False
    report_id = report_data["id"]

    # 2. Confirm Report via POST /report/confirm
    confirm_res = await async_client.post(
        "/report/confirm",
        json={
            "report_id": report_id,
            "officer_id": "OFFICER-99",
            "officer_notes": "All checks validated and approved.",
            "confirmed_verdict": "COMPLIANT",
        },
    )
    assert confirm_res.status_code == 200
    confirmed_data = confirm_res.json()
    assert confirmed_data["officer_confirmed"] is True
    assert confirmed_data["officer_id"] == "OFFICER-99"
    assert confirmed_data["officer_notes"] == "All checks validated and approved."
    assert confirmed_data["overall_verdict"] == "COMPLIANT"
    assert confirmed_data["confirmed_at"] is not None
