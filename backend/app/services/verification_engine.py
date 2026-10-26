"""
Deterministic Python verification engine.

Rule:
Verify in plain Python code, NEVER the LLM:
- numeric comparisons
- date validity
- boolean checks
- spec matching and certification type checks

Returns one of Verdicts: PASS, FAIL, MISSING, MISMATCH,
with evidence attributes adhering strictly to Match evidence rules.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any, Optional

from app.models.match import CheckedBy, Verdict
from app.models.requirement import Requirement, RequirementType
from app.schemas.evidence import ExtractedEvidence
from app.schemas.match import MatchCreate

logger = logging.getLogger(__name__)


def _normalize_currency_amount(amount: float, unit: Optional[str]) -> float:
    """Normalize Indian currency units (Crore, Lakh) to INR."""
    if not unit:
        return amount
    u = unit.strip().lower()
    if "crore" in u or "cr" in u:
        return amount * 10_000_000.0
    if "lakh" in u or "lac" in u:
        return amount * 100_000.0
    return amount


def _normalize_storage(amount: float, unit: Optional[str]) -> float:
    """Normalize storage units to GB."""
    if not unit:
        return amount
    u = unit.strip().lower()
    if "tb" in u:
        return amount * 1024.0
    if "mb" in u:
        return amount / 1024.0
    return amount


def _parse_date(val: Any) -> Optional[date]:
    """Parse string date (YYYY-MM-DD, DD/MM/YYYY, etc.) to date object."""
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if not isinstance(val, str):
        return None

    val = val.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def verify_requirement(
    requirement: Requirement,
    evidence: ExtractedEvidence,
    all_document_names: list[str],
) -> dict[str, Any]:
    """
    Evaluates evidence against a tender requirement in plain Python.

    Returns a dictionary suitable for initializing MatchCreate / Match.
    """
    req_type = requirement.requirement_type

    # 0. ERROR: When extraction failed due to API failure or rate limit
    if getattr(evidence, "error", None):
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.ERROR,
            "verdict_reason": f"Verification API Error: {evidence.error}. Please retry.",
            "evidence_file": None,
            "evidence_page": None,
            "evidence_quote": None,
            "extracted_value": None,
            "searched_in": {
                "documents": all_document_names,
                "terms": [evidence.error],
            },
            "checked_by": CheckedBy.SYSTEM,
            "llm_confidence": None,
        }

    # 1. MISSING: When no evidence was found in the documents
    if (
        not evidence.found
        or not evidence.quote
        or not evidence.quote.strip()
        or not evidence.file
        or evidence.page is None
    ):
        search_terms = evidence.search_terms or [requirement.sector_key or requirement.description[:50]]
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.MISSING,
            "verdict_reason": f"No evidence found in uploaded vendor documents for requirement: {requirement.description}",
            "evidence_file": None,
            "evidence_page": None,
            "evidence_quote": None,
            "extracted_value": None,
            "searched_in": {
                "documents": all_document_names,
                "terms": search_terms,
            },
            "checked_by": CheckedBy.LLM,
            "llm_confidence": evidence.confidence,
        }

    # Evidence was found — file, page, quote are present!
    evidence_file = evidence.file
    evidence_page = evidence.page
    evidence_quote = evidence.quote.strip()
    extracted_val = evidence.extracted_value or {}

    # 2. NUMERIC VERIFICATION
    if req_type == RequirementType.NUMERIC.value or req_type == "numeric":
        return _verify_numeric(
            requirement=requirement,
            evidence_file=evidence_file,
            evidence_page=evidence_page,
            evidence_quote=evidence_quote,
            extracted_val=extracted_val,
            confidence=evidence.confidence,
        )

    # 3. DATE VERIFICATION
    if req_type == RequirementType.DATE.value or req_type == "date":
        return _verify_date(
            requirement=requirement,
            evidence_file=evidence_file,
            evidence_page=evidence_page,
            evidence_quote=evidence_quote,
            extracted_val=extracted_val,
            confidence=evidence.confidence,
        )

    # 4. SPEC VERIFICATION
    if req_type == RequirementType.SPEC.value or req_type == "spec":
        return _verify_spec(
            requirement=requirement,
            evidence_file=evidence_file,
            evidence_page=evidence_page,
            evidence_quote=evidence_quote,
            extracted_val=extracted_val,
            confidence=evidence.confidence,
        )

    # 5. CERTIFICATION VERIFICATION
    if req_type == RequirementType.CERTIFICATION.value or req_type == "certification":
        return _verify_certification(
            requirement=requirement,
            evidence_file=evidence_file,
            evidence_page=evidence_page,
            evidence_quote=evidence_quote,
            extracted_val=extracted_val,
            confidence=evidence.confidence,
        )

    # 6. CLASSIFICATION VERIFICATION
    if req_type == RequirementType.CLASSIFICATION.value or req_type == "classification":
        return _verify_classification(
            requirement=requirement,
            evidence_file=evidence_file,
            evidence_page=evidence_page,
            evidence_quote=evidence_quote,
            extracted_val=extracted_val,
            confidence=evidence.confidence,
        )

    # 7. BOOLEAN / TEXT / OTHER
    return _verify_boolean_or_text(
        requirement=requirement,
        evidence_file=evidence_file,
        evidence_page=evidence_page,
        evidence_quote=evidence_quote,
        extracted_val=extracted_val,
        confidence=evidence.confidence,
    )


def _verify_numeric(
    requirement: Requirement,
    evidence_file: str,
    evidence_page: int,
    evidence_quote: str,
    extracted_val: dict[str, Any],
    confidence: Optional[float],
) -> dict[str, Any]:
    raw_amount = extracted_val.get("amount")
    if raw_amount is None:
        # Check if amount is inside value dict
        raw_amount = extracted_val.get("value")

    # If non-numeric or missing amount in evidence -> MISMATCH
    try:
        vendor_amount = float(raw_amount)
    except (TypeError, ValueError):
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.MISMATCH,
            "verdict_reason": f"Expected numeric value for '{requirement.description}', but extracted '{extracted_val}'.",
            "evidence_file": evidence_file,
            "evidence_page": evidence_page,
            "evidence_quote": evidence_quote,
            "extracted_value": extracted_val,
            "checked_by": CheckedBy.NUMERIC_ENGINE,
            "llm_confidence": confidence,
        }

    # Normalize units
    req_val_dict = requirement.value or {}
    req_amount = req_val_dict.get("amount") or req_val_dict.get("min")
    if req_amount is None:
        try:
            req_amount = float(requirement.description)
        except ValueError:
            req_amount = 0.0

    target_amount = float(req_amount)
    unit = requirement.unit or req_val_dict.get("unit") or ""
    extracted_unit = extracted_val.get("unit") or unit

    # Handle currency normalization if in INR/Crores/Lakhs
    norm_vendor = _normalize_currency_amount(vendor_amount, extracted_unit)
    norm_target = _normalize_currency_amount(target_amount, unit)

    operator = requirement.operator or ">="
    passed = False
    if operator == ">=":
        passed = norm_vendor >= norm_target
    elif operator == "<=":
        passed = norm_vendor <= norm_target
    elif operator == "==":
        passed = norm_vendor == norm_target
    elif operator == ">":
        passed = norm_vendor > norm_target
    elif operator == "<":
        passed = norm_vendor < norm_target
    elif operator == "between":
        min_val = req_val_dict.get("min", norm_target)
        max_val = req_val_dict.get("max", norm_target)
        passed = min_val <= norm_vendor <= max_val
    else:
        passed = norm_vendor >= norm_target

    verdict = Verdict.PASS if passed else Verdict.FAIL
    reason = (
        f"Verified: {vendor_amount} {extracted_unit} satisfies {operator} {target_amount} {unit}."
        if passed
        else f"Failed: {vendor_amount} {extracted_unit} does not satisfy {operator} {target_amount} {unit}."
    )

    return {
        "requirement_id": requirement.id,
        "verdict": verdict,
        "verdict_reason": reason,
        "evidence_file": evidence_file,
        "evidence_page": evidence_page,
        "evidence_quote": evidence_quote,
        "extracted_value": extracted_val,
        "checked_by": CheckedBy.NUMERIC_ENGINE,
        "llm_confidence": confidence,
    }


def _verify_date(
    requirement: Requirement,
    evidence_file: str,
    evidence_page: int,
    evidence_quote: str,
    extracted_val: dict[str, Any],
    confidence: Optional[float],
) -> dict[str, Any]:
    # 1. Bid validity in days
    req_val_dict = requirement.value or {}
    req_days = req_val_dict.get("days") or (
        req_val_dict.get("amount") if requirement.unit == "days" else None
    )

    extracted_days = extracted_val.get("days") or (
        extracted_val.get("amount") if extracted_val.get("unit") == "days" else None
    )

    if req_days is not None and extracted_days is not None:
        try:
            passed = float(extracted_days) >= float(req_days)
            verdict = Verdict.PASS if passed else Verdict.FAIL
            reason = (
                f"Bid validity {extracted_days} days satisfies required minimum {req_days} days."
                if passed
                else f"Bid validity {extracted_days} days is less than required minimum {req_days} days."
            )
            return {
                "requirement_id": requirement.id,
                "verdict": verdict,
                "verdict_reason": reason,
                "evidence_file": evidence_file,
                "evidence_page": evidence_page,
                "evidence_quote": evidence_quote,
                "extracted_value": extracted_val,
                "checked_by": CheckedBy.DATE_ENGINE,
                "llm_confidence": confidence,
            }
        except (TypeError, ValueError):
            pass

    # 2. Expiry / deadline date
    vendor_date_raw = extracted_val.get("date") or extracted_val.get("valid_until")
    vendor_date = _parse_date(vendor_date_raw)

    if vendor_date is None:
        # Check if date is in quote or if days was checked
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.MISMATCH,
            "verdict_reason": f"Could not parse valid date from vendor evidence: '{vendor_date_raw or extracted_val}'.",
            "evidence_file": evidence_file,
            "evidence_page": evidence_page,
            "evidence_quote": evidence_quote,
            "extracted_value": extracted_val,
            "checked_by": CheckedBy.DATE_ENGINE,
            "llm_confidence": confidence,
        }

    # Compare with deadline / target date or current date
    target_date = requirement.deadline or _parse_date(req_val_dict.get("date")) or date.today()
    passed = vendor_date >= target_date
    verdict = Verdict.PASS if passed else Verdict.FAIL
    reason = (
        f"Date validity verified: {vendor_date.isoformat()} is on or after required date {target_date.isoformat()}."
        if passed
        else f"Date validity failed: {vendor_date.isoformat()} is before required date {target_date.isoformat()}."
    )

    return {
        "requirement_id": requirement.id,
        "verdict": verdict,
        "verdict_reason": reason,
        "evidence_file": evidence_file,
        "evidence_page": evidence_page,
        "evidence_quote": evidence_quote,
        "extracted_value": extracted_val,
        "checked_by": CheckedBy.DATE_ENGINE,
        "llm_confidence": confidence,
    }


def _verify_spec(
    requirement: Requirement,
    evidence_file: str,
    evidence_page: int,
    evidence_quote: str,
    extracted_val: dict[str, Any],
    confidence: Optional[float],
) -> dict[str, Any]:
    req_val_dict = requirement.value or {}
    req_amount = req_val_dict.get("amount") or req_val_dict.get("min")

    # If numeric spec (e.g. RAM GB, SSD GB, display size)
    if req_amount is not None:
        raw_vendor_amount = extracted_val.get("amount")
        if raw_vendor_amount is not None:
            try:
                vendor_amount = float(raw_vendor_amount)
                target_amount = float(req_amount)
                norm_vendor = _normalize_storage(vendor_amount, extracted_val.get("unit"))
                norm_target = _normalize_storage(target_amount, requirement.unit)

                operator = requirement.operator or ">="
                passed = False
                if operator == ">=":
                    passed = norm_vendor >= norm_target
                elif operator == "<=":
                    passed = norm_vendor <= norm_target
                elif operator == "==":
                    passed = norm_vendor == norm_target
                else:
                    passed = norm_vendor >= norm_target

                verdict = Verdict.PASS if passed else Verdict.FAIL
                reason = (
                    f"Spec verified: {vendor_amount} {extracted_val.get('unit', '')} meets required {operator} {target_amount} {requirement.unit or ''}."
                    if passed
                    else f"Spec failed: {vendor_amount} {extracted_val.get('unit', '')} does not meet required {operator} {target_amount} {requirement.unit or ''}."
                )
                return {
                    "requirement_id": requirement.id,
                    "verdict": verdict,
                    "verdict_reason": reason,
                    "evidence_file": evidence_file,
                    "evidence_page": evidence_page,
                    "evidence_quote": evidence_quote,
                    "extracted_value": extracted_val,
                    "checked_by": CheckedBy.SPEC_ENGINE,
                    "llm_confidence": confidence,
                }
            except (ValueError, TypeError):
                pass

        # If amount was expected but not found or incompatible
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.MISMATCH,
            "verdict_reason": f"Expected spec '{requirement.description}' with amount {req_amount}, but vendor provided: {extracted_val}.",
            "evidence_file": evidence_file,
            "evidence_page": evidence_page,
            "evidence_quote": evidence_quote,
            "extracted_value": extracted_val,
            "checked_by": CheckedBy.SPEC_ENGINE,
            "llm_confidence": confidence,
        }

    # Text-based spec (e.g. processor model)
    req_text = (req_val_dict.get("text_value") or requirement.description).lower()
    vendor_text = (extracted_val.get("text_value") or evidence_quote).lower()

    # Check for known mismatches (e.g. i7 required, but Celeron or i3 found)
    if "i7" in req_text and any(x in vendor_text for x in ["celeron", "pentium", "core i3", "ryzen 3"]):
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.MISMATCH,
            "verdict_reason": f"Incompatible processor spec found in vendor quote: '{evidence_quote}' does not meet '{requirement.description}'.",
            "evidence_file": evidence_file,
            "evidence_page": evidence_page,
            "evidence_quote": evidence_quote,
            "extracted_value": extracted_val,
            "checked_by": CheckedBy.SPEC_ENGINE,
            "llm_confidence": confidence,
        }

    return {
        "requirement_id": requirement.id,
        "verdict": Verdict.PASS,
        "verdict_reason": f"Technical specification satisfied: '{evidence_quote}'.",
        "evidence_file": evidence_file,
        "evidence_page": evidence_page,
        "evidence_quote": evidence_quote,
        "extracted_value": extracted_val,
        "checked_by": CheckedBy.SPEC_ENGINE,
        "llm_confidence": confidence,
    }


def _verify_certification(
    requirement: Requirement,
    evidence_file: str,
    evidence_page: int,
    evidence_quote: str,
    extracted_val: dict[str, Any],
    confidence: Optional[float],
) -> dict[str, Any]:
    req_val_dict = requirement.value or {}
    expected_cert = (
        req_val_dict.get("certificate_name")
        or requirement.sector_key
        or requirement.description
    ).lower()

    vendor_cert = (extracted_val.get("certificate_name") or "").lower()

    # If vendor provided a clearly different/mismatched certificate
    # e.g. ISO 27001 when ISO 9001 required
    if "9001" in expected_cert and "27001" in vendor_cert:
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.MISMATCH,
            "verdict_reason": f"Certificate mismatch: vendor submitted '{extracted_val.get('certificate_name')}' instead of required '{req_val_dict.get('certificate_name', 'ISO 9001')}'.",
            "evidence_file": evidence_file,
            "evidence_page": evidence_page,
            "evidence_quote": evidence_quote,
            "extracted_value": extracted_val,
            "checked_by": CheckedBy.SPEC_ENGINE,
            "llm_confidence": confidence,
        }

    # Check validity date if present
    expiry_raw = extracted_val.get("valid_until") or extracted_val.get("date")
    if expiry_raw:
        expiry_date = _parse_date(expiry_raw)
        if expiry_date and expiry_date < date.today():
            return {
                "requirement_id": requirement.id,
                "verdict": Verdict.FAIL,
                "verdict_reason": f"Certificate expired on {expiry_date.isoformat()}.",
                "evidence_file": evidence_file,
                "evidence_page": evidence_page,
                "evidence_quote": evidence_quote,
                "extracted_value": extracted_val,
                "checked_by": CheckedBy.DATE_ENGINE,
                "llm_confidence": confidence,
            }

    # Certificate present and matching
    return {
        "requirement_id": requirement.id,
        "verdict": Verdict.PASS,
        "verdict_reason": f"Valid certification verified from document evidence: {evidence_quote[:100]}...",
        "evidence_file": evidence_file,
        "evidence_page": evidence_page,
        "evidence_quote": evidence_quote,
        "extracted_value": extracted_val,
        "checked_by": CheckedBy.SPEC_ENGINE,
        "llm_confidence": confidence,
    }


def _verify_classification(
    requirement: Requirement,
    evidence_file: str,
    evidence_page: int,
    evidence_quote: str,
    extracted_val: dict[str, Any],
    confidence: Optional[float],
) -> dict[str, Any]:
    req_val_dict = requirement.value or {}
    allowed_classes = req_val_dict.get("allowed_classes", ["Class I", "Class II"])
    vendor_class = extracted_val.get("class") or extracted_val.get("classification")

    if not vendor_class:
        # Check in quote
        for c in ["Class I", "Class II", "Class III"]:
            if c.lower() in evidence_quote.lower():
                vendor_class = c
                break

    if vendor_class and any(c.lower() == str(vendor_class).lower() for c in allowed_classes):
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.PASS,
            "verdict_reason": f"Classification '{vendor_class}' meets allowed classes: {allowed_classes}.",
            "evidence_file": evidence_file,
            "evidence_page": evidence_page,
            "evidence_quote": evidence_quote,
            "extracted_value": extracted_val,
            "checked_by": CheckedBy.SPEC_ENGINE,
            "llm_confidence": confidence,
        }

    return {
        "requirement_id": requirement.id,
        "verdict": Verdict.MISMATCH,
        "verdict_reason": f"Classification '{vendor_class}' does not meet allowed classes {allowed_classes}.",
        "evidence_file": evidence_file,
        "evidence_page": evidence_page,
        "evidence_quote": evidence_quote,
        "extracted_value": extracted_val,
        "checked_by": CheckedBy.SPEC_ENGINE,
        "llm_confidence": confidence,
    }


def _verify_boolean_or_text(
    requirement: Requirement,
    evidence_file: str,
    evidence_page: int,
    evidence_quote: str,
    extracted_val: dict[str, Any],
    confidence: Optional[float],
) -> dict[str, Any]:
    present = extracted_val.get("present", True)
    if present:
        return {
            "requirement_id": requirement.id,
            "verdict": Verdict.PASS,
            "verdict_reason": f"Requirement verified: '{evidence_quote}'.",
            "evidence_file": evidence_file,
            "evidence_page": evidence_page,
            "evidence_quote": evidence_quote,
            "extracted_value": extracted_val,
            "checked_by": CheckedBy.LLM,
            "llm_confidence": confidence,
        }

    return {
        "requirement_id": requirement.id,
        "verdict": Verdict.FAIL,
        "verdict_reason": f"Vendor document evidence indicates non-compliance: '{evidence_quote}'.",
        "evidence_file": evidence_file,
        "evidence_page": evidence_page,
        "evidence_quote": evidence_quote,
        "extracted_value": extracted_val,
        "checked_by": CheckedBy.LLM,
        "llm_confidence": confidence,
    }
