import uuid
import pytest
from pydantic import ValidationError

from app.models.match import CheckedBy, Verdict
from app.schemas.match import MatchCreate


def test_verdict_pass_with_complete_evidence():
    match = MatchCreate(
        requirement_id=uuid.uuid4(),
        verdict=Verdict.PASS,
        verdict_reason="RAM requirement satisfied (16 GB installed).",
        evidence_file="vendor_bid_specs.pdf",
        evidence_page=4,
        evidence_quote="System configured with 16 GB DDR5 RAM.",
        checked_by=CheckedBy.SPEC_ENGINE,
        extracted_value={"amount": 16, "unit": "GB"},
    )
    assert match.verdict == Verdict.PASS
    assert match.evidence_file == "vendor_bid_specs.pdf"
    assert match.evidence_page == 4


@pytest.mark.parametrize("verdict", [Verdict.PASS, Verdict.FAIL, Verdict.MISMATCH])
def test_verdict_requiring_evidence_fails_when_missing(verdict: Verdict):
    # Missing evidence_file, evidence_page, evidence_quote
    with pytest.raises(ValidationError) as exc:
        MatchCreate(
            requirement_id=uuid.uuid4(),
            verdict=verdict,
            verdict_reason="Reason without evidence",
            checked_by=CheckedBy.NUMERIC_ENGINE,
        )
    assert "requires evidence fields" in str(exc.value)


def test_verdict_missing_succeeds_with_searched_in():
    match = MatchCreate(
        requirement_id=uuid.uuid4(),
        verdict=Verdict.MISSING,
        verdict_reason="No OEM Authorization Letter found in uploaded vendor documents.",
        searched_in={
            "documents": ["technical_bid.pdf", "compliance_sheet.pdf"],
            "terms": ["OEM Authorization", "Manufacturer Authorization", "MAF"],
        },
        checked_by=CheckedBy.LLM,
    )
    assert match.verdict == Verdict.MISSING
    assert match.evidence_file is None
    assert match.evidence_page is None
    assert "technical_bid.pdf" in match.searched_in["documents"]


def test_verdict_missing_fails_without_searched_in():
    with pytest.raises(ValidationError) as exc:
        MatchCreate(
            requirement_id=uuid.uuid4(),
            verdict=Verdict.MISSING,
            verdict_reason="Document missing without searched_in details",
            checked_by=CheckedBy.LLM,
        )
        assert "requires 'searched_in'" in str(exc.value)


def test_verdict_error_succeeds_without_evidence():
    match = MatchCreate(
        requirement_id=uuid.uuid4(),
        verdict=Verdict.ERROR,
        verdict_reason="API call failed: 429 RESOURCE_EXHAUSTED. Please retry.",
        checked_by=CheckedBy.SYSTEM,
    )
    assert match.verdict == Verdict.ERROR
    assert match.evidence_file is None

