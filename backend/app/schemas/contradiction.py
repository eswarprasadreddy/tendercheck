from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ContradictionItem(BaseModel):
    field: str
    doc_a_filename: str
    doc_a_value: str
    doc_b_filename: str
    doc_b_value: str
    description: Optional[str] = None


class ContradictionList(BaseModel):
    contradictions: list[ContradictionItem] = Field(default_factory=list)


class ContradictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    vendor_name: str
    field: str
    doc_a_id: uuid.UUID
    doc_a_filename: str
    doc_a_value: str
    doc_b_id: uuid.UUID
    doc_b_filename: str
    doc_b_value: str
    description: Optional[str] = None
    created_at: datetime
