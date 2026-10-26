from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ExtractedEvidence(BaseModel):
    """
    Evidence located in vendor documents by Gemini.
    Must contain file, page, quote, and extracted_value.
    """
    found: bool = True
    file: Optional[str] = None
    page: Optional[int] = None
    quote: Optional[str] = None
    extracted_value: Optional[dict[str, Any]] = None
    search_terms: list[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    error: Optional[str] = None

