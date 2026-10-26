"""
Pydantic schemas for Match verification records.

Evidence rules (enforced at the schema layer):
  - PASS, FAIL, MISMATCH: evidence_file, evidence_page, and evidence_quote are REQUIRED.
  - MISSING: searched_in is REQUIRED (documents and terms checked); evidence fields are optional/null.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.match import CheckedBy, Verdict


class MatchBase(BaseModel):
    requirement_id: uuid.UUID
    vendor_document_id: Optional[uuid.UUID] = None
    verdict: Verdict
    verdict_reason: str
    evidence_file: Optional[str] = None
    evidence_page: Optional[int] = Field(default=None, ge=1)
    evidence_quote: Optional[str] = None
    extracted_value: Optional[dict[str, Any]] = None
    searched_in: Optional[dict[str, Any]] = None
    checked_by: CheckedBy
    llm_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_evidence_rules(self) -> "MatchBase":
        """
        Enforce:
        - PASS / FAIL / MISMATCH: evidence_file, evidence_page, evidence_quote required.
        - MISSING: searched_in required; evidence columns may be null.
        """
        evidence_required_verdicts = {Verdict.PASS, Verdict.FAIL, Verdict.MISMATCH}

        if self.verdict in evidence_required_verdicts:
            missing_fields: list[str] = []
            if not self.evidence_file:
                missing_fields.append("evidence_file")
            if self.evidence_page is None:
                missing_fields.append("evidence_page")
            if not self.evidence_quote:
                missing_fields.append("evidence_quote")

            if missing_fields:
                raise ValueError(
                    f"Verdict '{self.verdict.value}' requires evidence fields: {', '.join(missing_fields)}"
                )

        elif self.verdict == Verdict.MISSING:
            if not self.searched_in:
                raise ValueError(
                    "Verdict 'MISSING' requires 'searched_in' specifying the documents and search terms checked."
                )

        return self


from app.schemas.requirement import RequirementResponse


class MatchCreate(MatchBase):
    pass


class MatchResponse(MatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    requirement: Optional[RequirementResponse] = None


class MatchVerdictUpdate(BaseModel):
    verdict: Verdict
    officer_notes: Optional[str] = None

