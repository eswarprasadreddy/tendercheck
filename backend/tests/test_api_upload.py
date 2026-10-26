import io
import uuid
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.tenders import _process_tender
from app.models.tender import Tender, TenderStatus
from app.models.requirement import Requirement
from app.services.requirement_parser import RequirementParser


@pytest.mark.asyncio
async def test_upload_non_pdf_fails(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/tenders/upload",
        data={"title": "Test Tender", "reference_number": "GEM/2026/B/0001"},
        files={"file": ("tender.txt", b"Not a PDF content", "text/plain")},
    )
    assert response.status_code == 422
    assert "Only PDF files are accepted" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_valid_pdf_and_duplicate_handling(
    async_client: AsyncClient,
    sample_pdf_path: Path,
):
    with open(sample_pdf_path, "rb") as fh:
        pdf_bytes = fh.read()

    ref_num = f"GEM/2026/B/{uuid.uuid4().hex[:8].upper()}"

    # 1. Successful upload
    response = await async_client.post(
        "/api/v1/tenders/upload",
        data={"title": "NIC Commercial Laptop Tender", "reference_number": ref_num},
        files={"file": ("tender.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["reference_number"] == ref_num
    assert data["status"] == "uploaded"
    assert "id" in data
    tender_id = data["id"]

    # 2. Duplicate reference number returns 409
    dup_response = await async_client.post(
        "/api/v1/tenders/upload",
        data={"title": "Duplicate Tender", "reference_number": ref_num},
        files={"file": ("tender.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert dup_response.status_code == 409
    assert "already exists" in dup_response.json()["detail"]

    # 3. GET tender returns metadata
    get_res = await async_client.get(f"/api/v1/tenders/{tender_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == tender_id
    assert get_res.json()["status"] == "uploaded"

    # 4. GET requirements before parsing returns 425
    early_res = await async_client.get(f"/api/v1/tenders/{tender_id}/requirements")
    assert early_res.status_code == 425


@pytest.mark.asyncio
async def test_process_tender_and_list_requirements(
    async_client: AsyncClient,
    db_session: AsyncSession,
    sample_pdf_path: Path,
    sample_extracted_requirements_json: str,
):
    # 1. Create tender in DB
    ref_num = f"GEM/2026/B/{uuid.uuid4().hex[:8].upper()}"
    tender = Tender(
        title="Laptop Procurement GeM Tender",
        reference_number=ref_num,
        pdf_path=str(sample_pdf_path),
        status=TenderStatus.UPLOADED.value,
    )
    db_session.add(tender)
    await db_session.commit()
    await db_session.refresh(tender)

    # 2. Run _process_tender with mocked Gemini client
    mock_client = MagicMock()
    mock_client.generate_json.return_value = sample_extracted_requirements_json
    mock_parser = RequirementParser(client=mock_client, sector_id="it_hardware")

    await _process_tender(
        tender_id=tender.id,
        pdf_path=sample_pdf_path,
        session=db_session,
        parser=mock_parser,
    )

    # 3. Verify tender status updated to PARSED
    await db_session.refresh(tender)
    assert tender.status == TenderStatus.PARSED.value
    assert tender.page_count == 3
    assert "[Page 1]" in tender.raw_text
    assert "[Page 2]" in tender.raw_text
    assert "[Page 3]" in tender.raw_text

    # 4. Verify requirements persisted to database
    req_rows = await db_session.scalars(
        select(Requirement).where(Requirement.tender_id == tender.id)
    )
    reqs = list(req_rows)
    assert len(reqs) >= 10

    # 5. Query via GET /api/v1/tenders/{id}/requirements endpoint
    res = await async_client.get(f"/api/v1/tenders/{tender.id}/requirements")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == len(reqs)

    # Check key requirements are present in the response
    sector_keys = {item["sector_key"] for item in items if item["sector_key"]}
    assert "annual_turnover" in sector_keys
    assert "ram_gb" in sector_keys
    assert "ssd_gb" in sector_keys
    assert "processor" in sector_keys
    assert "display_inches" in sector_keys
    assert "warranty_years" in sector_keys
    assert "iso_9001" in sector_keys
    assert "bis_registration" in sector_keys
    assert "oem_authorization" in sector_keys
    assert "make_in_india" in sector_keys
    assert "bid_validity" in sector_keys
