"""
Pydantic schemas for Requirement — both API I/O and LLM JSON output validation.

Value payload shapes
--------------------
The LLM is instructed to return one of these shapes depending on requirement_type.
The ``LLMRequirement`` model is what the LLM must produce and what we validate
against.  The DB model stores the raw dict in the JSON column.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ------------------------------------------------------------------ #
# Value payload schemas                                                 #
# ------------------------------------------------------------------ #


class NumericValue(BaseModel):
    """For numeric: turnover, experience years, order count, similar orders."""
    amount: Optional[float] = None
    unit: str  # e.g. "INR", "years", "orders", "employees"
    min: Optional[float] = None  # for "between" operator
    max: Optional[float] = None  # for "between" operator


class DateValue(BaseModel):
    """For date: validity dates, bid deadline."""
    date: Optional[date] = None          # exact date
    not_before: Optional[date] = None    # certificate must be valid on/after
    not_after: Optional[date] = None     # certificate must expire on/before


class BooleanValue(BaseModel):
    """For boolean: document presence check."""
    required: bool = True


class SpecValue(BaseModel):
    """
    For spec: hardware specs like RAM ≥ 16 GB, SSD ≥ 512 GB.
    Either a numeric threshold or an exact text value (e.g. processor model).
    """
    amount: Optional[float] = None
    unit: Optional[str] = None       # "GB", "inches", "GHz"
    min: Optional[float] = None
    max: Optional[float] = None
    text_value: Optional[str] = None  # e.g. "Intel Core i7 13th gen or higher"


class CertificationValue(BaseModel):
    """
    For certification: ISO, BIS, MSME, OEM auth, Make in India cert.
    Presence is always required; validity date is checked by the date engine.
    """
    certificate_name: str              # canonical name, e.g. "ISO 9001:2015"
    required: bool = True
    valid_as_of: Optional[date] = None  # must be valid on this date (bid date)


class ClassificationValue(BaseModel):
    """
    For classification: Make in India local content class, MSME category.
    """
    field_name: str                   # e.g. "make_in_india_class", "msme_category"
    allowed_classes: list[str]        # e.g. ["Class I", "Class II"]


class TextValue(BaseModel):
    """For text: pattern match or allowed values list."""
    pattern: Optional[str] = None                  # regex pattern
    allowed_values: Optional[list[str]] = None     # exact match list


AnyValue = Union[
    NumericValue,
    DateValue,
    BooleanValue,
    SpecValue,
    CertificationValue,
    ClassificationValue,
    TextValue,
]

# ------------------------------------------------------------------ #
# LLM output schema — what the LLM must produce and we validate       #
# ------------------------------------------------------------------ #


class LLMRequirement(BaseModel):
    """
    Schema the LLM must return for each requirement.
    Validated immediately after receiving the LLM JSON response.
    """
    category: Literal[
        "financial", "experience", "legal", "certification",
        "technical_spec", "delivery", "compliance", "other",
    ]
    description: str
    requirement_type: Literal[
        "numeric", "date", "boolean", "spec",
        "certification", "classification", "text",
    ]
    operator: Optional[Literal[">=", "<=", "==", ">", "<", "between", "exists", "regex"]] = None
    value: Optional[dict[str, Any]] = None
    unit: Optional[str] = None
    source_page: int = Field(ge=1)
    source_quote: str
    is_mandatory: bool = True
    llm_confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    sector_key: Optional[str] = None

    @model_validator(mode="after")
    def validate_type_operator_coherence(self) -> "LLMRequirement":
        """Basic sanity checks without doing the actual comparison (that's the engine's job)."""
        numeric_types = {"numeric", "spec"}
        if self.requirement_type in numeric_types and self.operator is None:
            # Default to >= for numeric specs if the LLM forgot
            self.operator = ">="
        if self.requirement_type == "boolean" and self.value is None:
            self.value = {"required": True}
        if self.requirement_type == "certification" and self.value is None:
            self.value = {"certificate_name": self.description, "required": True}
        return self


class LLMRequirementList(BaseModel):
    """Top-level wrapper expected from the LLM."""
    requirements: list[LLMRequirement]


# ------------------------------------------------------------------ #
# API response schema                                                   #
# ------------------------------------------------------------------ #


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tender_id: uuid.UUID
    category: str
    description: str
    requirement_type: str
    operator: Optional[str]
    value: Optional[dict[str, Any]]
    unit: Optional[str]
    source_page: int
    source_quote: str
    llm_confidence: Optional[float]
    is_mandatory: bool
    sector_key: Optional[str]
    created_at: datetime


class RequirementUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    requirement_type: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[dict[str, Any]] = None
    unit: Optional[str] = None
    source_page: Optional[int] = None
    source_quote: Optional[str] = None
    is_mandatory: Optional[bool] = None
    sector_key: Optional[str] = None


class RequirementCreate(BaseModel):
    category: str
    description: str
    requirement_type: str = "numeric"
    operator: Optional[str] = ">="
    value: Optional[dict[str, Any]] = None
    unit: Optional[str] = None
    source_page: int = 1
    source_quote: str = "Manually specified by Officer"
    is_mandatory: bool = True
    sector_key: Optional[str] = None

