"""
Tests for the matching engine, verdict types, and contradiction detection.

Required:
- One test per verdict type: PASS, FAIL, MISSING, MISMATCH
- One test for contradictions
- Strict verification of evidence rules and persistence to database
"""
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contradiction import Contradiction
from app.models.match import CheckedBy, Match, Verdict
from app.models.report import OverallVerdict, Report
from app.models.requirement import Requirement, RequirementCategory, RequirementType
from app.models.tender import Tender, TenderStatus
from app.models.vendor_document import VendorDocStatus, VendorDocument
from app.schemas.evidence import ExtractedEvidence
from app.services.contradiction_service import ContradictionDetector
from app.services.matching_engine import MatchingEngine
from app.services.report_service import confirm_report, generate_vendor_report
from app.services.verification_engine import verify_requirement


@pytest.mark.asyncio
async def test_verdict_pass(db_session: AsyncSession):
    """
    Test 1: Verdict PASS
    Vendor document satisfies numeric RAM requirement (16 GB required, 16 GB provided).
    Evidence rules require evidence_file, evidence_page, and evidence_quote.
    """
    tender = Tender(
        title="Laptop Procurement 2026",
        reference_number="GEM/2026/B/TEST-PASS",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.flush()

    req = Requirement(
        tender_id=tender.id,
        category=RequirementCategory.TECHNICAL_SPEC.value,
        description="Minimum 16 GB DDR4/DDR5 RAM",
        requirement_type=RequirementType.SPEC.value,
        operator=">=",
        value={"amount": 16.0, "unit": "GB"},
        unit="GB",
        source_page=2,
        source_quote="Minimum 16 GB DDR4/DDR5 3200MHz RAM.",
        is_mandatory=True,
    )
    db_session.add(req)

    v_doc = VendorDocument(
        tender_id=tender.id,
        vendor_name="Acme Infotech",
        original_filename="technical_bid.pdf",
        pdf_path="/tmp/technical_bid.pdf",
        raw_text="[Page 2]\nSystem is configured with 16 GB DDR5 RAM at 4800MHz.",
        page_count=3,
        status=VendorDocStatus.READY.value,
    )
    db_session.add(v_doc)
    await db_session.commit()

    # Evidence extracted
    evidence = ExtractedEvidence(
        found=True,
        file="technical_bid.pdf",
        page=2,
        quote="System is configured with 16 GB DDR5 RAM at 4800MHz.",
        extracted_value={"amount": 16.0, "unit": "GB"},
        confidence=0.98,
    )

    engine = MatchingEngine()
    matches = await engine.run_matching(
        db=db_session,
        tender_id=tender.id,
        vendor_name="Acme Infotech",
        custom_evidence_map={req.id: evidence},
    )

    assert len(matches) == 1
    m = matches[0]
    assert m.verdict == Verdict.PASS.value
    assert m.evidence_file == "technical_bid.pdf"
    assert m.evidence_page == 2
    assert "16 GB" in m.evidence_quote
    assert m.checked_by == CheckedBy.SPEC_ENGINE.value

    # Check persistence in database
    db_match = await db_session.get(Match, m.id)
    assert db_match is not None
    assert db_match.verdict == Verdict.PASS.value
    assert db_match.evidence_file == "technical_bid.pdf"
    assert db_match.evidence_page == 2
    assert db_match.evidence_quote is not None


@pytest.mark.asyncio
async def test_verdict_fail(db_session: AsyncSession):
    """
    Test 2: Verdict FAIL
    Vendor document provides 8 GB RAM when 16 GB is required.
    Evidence rules require evidence_file, evidence_page, and evidence_quote.
    """
    tender = Tender(
        title="Laptop Procurement 2026",
        reference_number="GEM/2026/B/TEST-FAIL",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.flush()

    req = Requirement(
        tender_id=tender.id,
        category=RequirementCategory.TECHNICAL_SPEC.value,
        description="Minimum 16 GB DDR4/DDR5 RAM",
        requirement_type=RequirementType.SPEC.value,
        operator=">=",
        value={"amount": 16.0, "unit": "GB"},
        unit="GB",
        source_page=2,
        source_quote="Minimum 16 GB DDR4/DDR5 3200MHz RAM.",
        is_mandatory=True,
    )
    db_session.add(req)

    v_doc = VendorDocument(
        tender_id=tender.id,
        vendor_name="LowSpec Tech",
        original_filename="bid_specs.pdf",
        pdf_path="/tmp/bid_specs.pdf",
        raw_text="[Page 1]\nHardware specification: 8 GB DDR4 RAM installed.",
        page_count=2,
        status=VendorDocStatus.READY.value,
    )
    db_session.add(v_doc)
    await db_session.commit()

    # Evidence indicates 8 GB
    evidence = ExtractedEvidence(
        found=True,
        file="bid_specs.pdf",
        page=1,
        quote="Hardware specification: 8 GB DDR4 RAM installed.",
        extracted_value={"amount": 8.0, "unit": "GB"},
        confidence=0.97,
    )

    engine = MatchingEngine()
    matches = await engine.run_matching(
        db=db_session,
        tender_id=tender.id,
        vendor_name="LowSpec Tech",
        custom_evidence_map={req.id: evidence},
    )

    assert len(matches) == 1
    m = matches[0]
    assert m.verdict == Verdict.FAIL.value
    assert m.evidence_file == "bid_specs.pdf"
    assert m.evidence_page == 1
    assert m.evidence_quote == "Hardware specification: 8 GB DDR4 RAM installed."
    assert "failed" in m.verdict_reason.lower() or "does not meet" in m.verdict_reason.lower()

    # Check persistence
    db_match = await db_session.get(Match, m.id)
    assert db_match is not None
    assert db_match.verdict == Verdict.FAIL.value
    assert db_match.evidence_file is not None
    assert db_match.evidence_page is not None
    assert db_match.evidence_quote is not None


@pytest.mark.asyncio
async def test_verdict_missing(db_session: AsyncSession):
    """
    Test 3: Verdict MISSING
    Vendor document lacks any OEM Authorization letter.
    Evidence rules require searched_in populated, evidence columns null.
    """
    tender = Tender(
        title="Laptop Procurement 2026",
        reference_number="GEM/2026/B/TEST-MISSING",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.flush()

    req = Requirement(
        tender_id=tender.id,
        category=RequirementCategory.CERTIFICATION.value,
        description="Non-OEM bidder must submit OEM Authorization Letter (MAF)",
        requirement_type=RequirementType.CERTIFICATION.value,
        operator="exists",
        value={"certificate_name": "OEM Authorization Letter", "required": True},
        source_page=3,
        source_quote="Bidders who are not OEMs must submit an authentic OEM Authorization Letter (MAF).",
        is_mandatory=True,
    )
    db_session.add(req)

    v_doc = VendorDocument(
        tender_id=tender.id,
        vendor_name="MissingMAF Corp",
        original_filename="company_profile.pdf",
        pdf_path="/tmp/company_profile.pdf",
        raw_text="[Page 1]\nCompany profile and financial credentials only.",
        page_count=1,
        status=VendorDocStatus.READY.value,
    )
    db_session.add(v_doc)
    await db_session.commit()

    # Evidence not found
    evidence = ExtractedEvidence(
        found=False,
        file=None,
        page=None,
        quote=None,
        extracted_value=None,
        search_terms=["OEM Authorization", "Manufacturer Authorization", "MAF"],
        confidence=0.99,
    )

    engine = MatchingEngine()
    matches = await engine.run_matching(
        db=db_session,
        tender_id=tender.id,
        vendor_name="MissingMAF Corp",
        custom_evidence_map={req.id: evidence},
    )

    assert len(matches) == 1
    m = matches[0]
    assert m.verdict == Verdict.MISSING.value
    assert m.evidence_file is None
    assert m.evidence_page is None
    assert m.evidence_quote is None
    assert m.searched_in is not None
    assert "company_profile.pdf" in m.searched_in["documents"]
    assert "OEM Authorization" in m.searched_in["terms"]

    # Check persistence
    db_match = await db_session.get(Match, m.id)
    assert db_match is not None
    assert db_match.verdict == Verdict.MISSING.value
    assert db_match.evidence_file is None
    assert db_match.searched_in is not None


@pytest.mark.asyncio
async def test_verdict_mismatch(db_session: AsyncSession):
    """
    Test 4: Verdict MISMATCH
    Vendor provides ISO 27001 certificate instead of required ISO 9001:2015.
    Evidence rules require evidence_file, evidence_page, and evidence_quote.
    """
    tender = Tender(
        title="Laptop Procurement 2026",
        reference_number="GEM/2026/B/TEST-MISMATCH",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.flush()

    req = Requirement(
        tender_id=tender.id,
        category=RequirementCategory.CERTIFICATION.value,
        description="OEM and Bidder must have valid ISO 9001:2015 certification",
        requirement_type=RequirementType.CERTIFICATION.value,
        operator="exists",
        value={"certificate_name": "ISO 9001:2015", "required": True},
        source_page=3,
        source_quote="The OEM and the Bidder must possess a valid ISO 9001:2015 quality certificate.",
        is_mandatory=True,
    )
    db_session.add(req)

    v_doc = VendorDocument(
        tender_id=tender.id,
        vendor_name="SecurityOnly Ltd",
        original_filename="iso_certificate.pdf",
        pdf_path="/tmp/iso_certificate.pdf",
        raw_text="[Page 1]\nCertificate of Registration: ISO 27001:2013 Information Security Management.",
        page_count=1,
        status=VendorDocStatus.READY.value,
    )
    db_session.add(v_doc)
    await db_session.commit()

    # Vendor submitted ISO 27001 instead of ISO 9001
    evidence = ExtractedEvidence(
        found=True,
        file="iso_certificate.pdf",
        page=1,
        quote="Certificate of Registration: ISO 27001:2013 Information Security Management.",
        extracted_value={"certificate_name": "ISO 27001:2013", "present": True},
        confidence=0.95,
    )

    engine = MatchingEngine()
    matches = await engine.run_matching(
        db=db_session,
        tender_id=tender.id,
        vendor_name="SecurityOnly Ltd",
        custom_evidence_map={req.id: evidence},
    )

    assert len(matches) == 1
    m = matches[0]
    assert m.verdict == Verdict.MISMATCH.value
    assert m.evidence_file == "iso_certificate.pdf"
    assert m.evidence_page == 1
    assert "ISO 27001:2013" in m.evidence_quote
    assert "mismatch" in m.verdict_reason.lower()

    # Check persistence
    db_match = await db_session.get(Match, m.id)
    assert db_match is not None
    assert db_match.verdict == Verdict.MISMATCH.value
    assert db_match.evidence_file == "iso_certificate.pdf"
    assert db_match.evidence_page == 1
    assert db_match.evidence_quote is not None


@pytest.mark.asyncio
async def test_contradiction_detection(db_session: AsyncSession):
    """
    Test 5: Contradiction Detection across Vendor Documents
    Doc A states turnover of INR 2.50 Crore and 150 employees.
    Doc B states turnover of INR 1.20 Crore and 25 employees.
    Saved to the contradictions table.
    """
    tender = Tender(
        title="Laptop Procurement 2026",
        reference_number="GEM/2026/B/TEST-CONTRADICTION",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.flush()

    doc_a = VendorDocument(
        tender_id=tender.id,
        vendor_name="Contradictory Systems",
        doc_type="balance_sheet",
        original_filename="audited_balance_sheet.pdf",
        pdf_path="/tmp/audited_balance_sheet.pdf",
        raw_text="The company recorded annual turnover of INR 2.50 Crore for FY 2024-25. Total staff comprises 150 full-time employees.",
        page_count=2,
        status=VendorDocStatus.READY.value,
    )
    doc_b = VendorDocument(
        tender_id=tender.id,
        vendor_name="Contradictory Systems",
        doc_type="undertaking",
        original_filename="vendor_undertaking.pdf",
        pdf_path="/tmp/vendor_undertaking.pdf",
        raw_text="Declaration: Average turnover is INR 1.20 Crore. Currently employing 25 personnel.",
        page_count=1,
        status=VendorDocStatus.READY.value,
    )
    db_session.add(doc_a)
    db_session.add(doc_b)
    await db_session.commit()

    detector = ContradictionDetector()
    contradictions = await detector.detect_and_save(
        db=db_session,
        tender_id=tender.id,
        vendor_name="Contradictory Systems",
        vendor_docs=[doc_a, doc_b],
    )

    assert len(contradictions) >= 1

    # Verify rows in the contradictions table
    saved = list(
        await db_session.scalars(
            select(Contradiction).where(
                Contradiction.tender_id == tender.id,
                Contradiction.vendor_name == "Contradictory Systems",
            )
        )
    )
    assert len(saved) >= 1
    fields = [c.field for c in saved]
    assert "annual_turnover" in fields or "employee_count" in fields

    # Verify fields of the first contradiction
    c0 = saved[0]
    assert c0.tender_id == tender.id
    assert c0.vendor_name == "Contradictory Systems"
    assert c0.doc_a_id in [doc_a.id, doc_b.id]
    assert c0.doc_b_id in [doc_a.id, doc_b.id]
    assert c0.doc_a_value != c0.doc_b_value


@pytest.mark.asyncio
async def test_report_generation_and_confirmation(db_session: AsyncSession):
    """
    Test 6: Report generation and officer confirmation.
    Confirms that officer confirmation via confirm_report is the ONLY way to finalize.
    """
    tender = Tender(
        title="Laptop Procurement 2026",
        reference_number="GEM/2026/B/TEST-REPORT",
        pdf_path="/tmp/tender.pdf",
        status=TenderStatus.PARSED.value,
    )
    db_session.add(tender)
    await db_session.flush()

    req = Requirement(
        tender_id=tender.id,
        category=RequirementCategory.TECHNICAL_SPEC.value,
        description="Minimum 16 GB DDR4/DDR5 RAM",
        requirement_type=RequirementType.SPEC.value,
        operator=">=",
        value={"amount": 16.0, "unit": "GB"},
        unit="GB",
        source_page=2,
        source_quote="Minimum 16 GB RAM.",
        is_mandatory=True,
    )
    db_session.add(req)
    await db_session.flush()

    # Create a PASS match
    match = Match(
        requirement_id=req.id,
        verdict=Verdict.PASS.value,
        verdict_reason="Satisfies RAM requirement",
        evidence_file="specs.pdf",
        evidence_page=1,
        evidence_quote="Installed 16 GB RAM",
        checked_by=CheckedBy.SPEC_ENGINE.value,
    )
    db_session.add(match)
    await db_session.commit()

    # Generate report
    report = await generate_vendor_report(
        db=db_session,
        tender_id=tender.id,
        vendor_name="Acme Infotech",
    )
    assert report.pass_count == 1
    assert report.fail_count == 0
    assert report.overall_verdict == OverallVerdict.COMPLIANT.value
    assert report.officer_confirmed is False
    assert report.confirmed_at is None

    # Confirm report
    confirmed = await confirm_report(
        db=db_session,
        report_id=report.id,
        officer_id="OFFICER-42",
        officer_notes="Verified by procurement officer and approved for technical evaluation.",
    )

    assert confirmed.officer_confirmed is True
    assert confirmed.officer_id == "OFFICER-42"
    assert confirmed.officer_notes == "Verified by procurement officer and approved for technical evaluation."
    assert confirmed.confirmed_at is not None
