from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VendorDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    vendor_name: str
    doc_type: Optional[str] = None
    original_filename: str
    pdf_path: str
    page_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
