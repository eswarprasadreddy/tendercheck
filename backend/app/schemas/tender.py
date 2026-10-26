"""
Pydantic schemas for Tender API I/O.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TenderCreate(BaseModel):
    title: str
    reference_number: str


class TenderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    reference_number: str
    pdf_path: str
    page_count: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
