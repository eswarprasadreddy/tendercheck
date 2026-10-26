from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.report import OverallVerdict
from app.schemas.contradiction import ContradictionResponse
from app.schemas.match import MatchResponse


class ReportConfirmRequest(BaseModel):
    report_id: Optional[uuid.UUID] = None
    officer_id: str
    officer_notes: Optional[str] = None
    confirmed_verdict: Optional[OverallVerdict] = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    vendor_name: str
    overall_verdict: str
    pass_count: int
    fail_count: int
    missing_count: int
    mismatch_count: int
    contradiction_count: int
    officer_confirmed: bool
    officer_notes: Optional[str] = None
    officer_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    matches: Optional[list[MatchResponse]] = None
    contradictions: Optional[list[ContradictionResponse]] = None
