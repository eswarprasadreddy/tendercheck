"""
All LLM prompt templates live here so they can be reviewed and iterated
without touching service logic.
"""
from __future__ import annotations

import json
from typing import Any


REQUIREMENT_EXTRACTION_SYSTEM = """\
You are a senior procurement compliance specialist with deep expertise in \
government tenders in India, especially on the Government e-Marketplace (GeM). \
Your task is to extract every eligibility and technical requirement from the \
tender document provided.

SECTOR: {sector_name}
{sector_hints}

OUTPUT FORMAT
-------------
Return a JSON object with a single key "requirements" whose value is an array.
Each element must match this schema exactly:

{{
  "category": <one of: "financial", "experience", "legal", "certification",
               "technical_spec", "delivery", "compliance", "other">,
  "description": <concise human-readable description of the requirement>,
  "requirement_type": <one of: "numeric", "date", "boolean", "spec",
                       "certification", "classification", "text">,
  "operator": <one of: ">=", "<=", "==", ">", "<", "between", "exists",
               "regex" | null for boolean/text>,
  "value": <structured payload — see VALUE FORMATS below>,
  "unit": <unit string if applicable, else null>,
  "source_page": <integer page number where this requirement appears, 1-indexed>,
  "source_quote": <verbatim excerpt from the tender that this requirement was derived from>,
  "is_mandatory": <true | false>,
  "llm_confidence": <float 0.0-1.0>,
  "sector_key": <canonical key from sector config if known, else null>
}}

VALUE FORMATS
-------------
numeric      : {{"amount": <float>, "unit": "<str>", "min": <float|null>, "max": <float|null>}}
date         : {{"date": "<YYYY-MM-DD>|null", "not_before": "<YYYY-MM-DD>|null", "not_after": "<YYYY-MM-DD>|null"}}
boolean      : {{"required": true}}
spec         : {{"amount": <float|null>, "unit": "<str|null>", "min": <float|null>, "text_value": "<str|null>"}}
certification: {{"certificate_name": "<str>", "required": true, "valid_as_of": "<YYYY-MM-DD|null>"}}
classification: {{"field_name": "<str>", "allowed_classes": ["<str>", ...]}}
text         : {{"pattern": "<regex|null>", "allowed_values": ["<str>", ...]|null}}

RULES
-----
1. Extract EVERY distinct requirement — do not merge or skip any.
2. For numeric thresholds (turnover, RAM, SSD) set the correct operator.
3. For certificates, use requirement_type "certification" and include the certificate name.
4. For Make in India class requirements, use requirement_type "classification".
5. Do NOT infer values not stated in the document.
6. source_quote must be the verbatim text from the tender (max 300 chars).
7. If MSME/Startup vendors are exempted from a requirement, set is_mandatory=false \
and note it in the description.
"""

REQUIREMENT_EXTRACTION_USER = """\
TENDER DOCUMENT TEXT (pages 1-{page_count}):

{tender_text}

Extract all requirements now.
"""


def format_sector_context(sector_config: dict[str, Any]) -> str:
    """Format arbitrary sector config metadata into prompt guidance."""
    parts: list[str] = []
    certs = sector_config.get("known_certificates", [])
    if certs:
        parts.append("Known Certificates (use matching sector_key if applicable):\n" + "\n".join(
            f"  • {c['name']} (sector_key='{c['key']}')" for c in certs
        ))
    specs = sector_config.get("known_specs", [])
    if specs:
        parts.append("Known Technical Specs:\n" + "\n".join(
            f"  • {s['name']} (sector_key='{s['key']}', default unit: {s.get('unit')})" for s in specs
        ))
    fin = sector_config.get("known_financial_fields", [])
    if fin:
        parts.append("Known Financial Fields:\n" + "\n".join(
            f"  • {f['name']} (sector_key='{f['key']}', unit: {f.get('unit')})" for f in fin
        ))
    exp = sector_config.get("known_experience_fields", [])
    if exp:
        parts.append("Known Experience Fields:\n" + "\n".join(
            f"  • {e['name']} (sector_key='{e['key']}', unit: {e.get('unit')})" for e in exp
        ))
    dates = sector_config.get("known_dates", [])
    if dates:
        parts.append("Known Dates / Deadlines:\n" + "\n".join(
            f"  • {d['name']} (sector_key='{d['key']}')" for d in dates
        ))
    hints = sector_config.get("prompt_hints", [])
    if hints:
        parts.append("Sector-Specific Hints:\n" + "\n".join(
            f"  • {h}" for h in hints
        ))
    return "\n\n".join(parts)


def build_requirement_extraction_prompt(
    tender_text: str,
    page_count: int,
    sector_config: dict[str, Any],
) -> str:
    """Assemble the final prompt string for requirement extraction."""
    sector_name = sector_config.get("sector_name", "General Procurement")
    sector_hints = format_sector_context(sector_config)

    system = REQUIREMENT_EXTRACTION_SYSTEM.format(
        sector_name=sector_name,
        sector_hints=sector_hints,
    )
    user = REQUIREMENT_EXTRACTION_USER.format(
        page_count=page_count,
        tender_text=tender_text,
    )
    return f"{system}\n\n{user}"


EVIDENCE_EXTRACTION_SYSTEM = """\
You are an expert procurement compliance analyst. Your job is to locate evidence in vendor bid documents for a specific tender requirement, and extract the claimed value.

REQUIREMENT TO VERIFY:
- Category: {category}
- Description: {description}
- Requirement Type: {requirement_type}
- Operator: {operator}
- Target Value: {target_value}
- Unit: {unit}

OUTPUT FORMAT
-------------
Return a JSON object matching this schema:
{{
  "found": <true if evidence/mention for this requirement was located in the documents, else false>,
  "file": <filename of the document where evidence was found, or null if not found>,
  "page": <integer 1-indexed page number where evidence quote appears, or null if not found>,
  "quote": <verbatim excerpt from the document containing the evidence (max 300 chars), or null if not found>,
  "extracted_value": <structured payload representing the extracted value or null if not found>,
  "search_terms": [<keywords used to search for this requirement, e.g. ["turnover", "revenue"]>],
  "confidence": <float 0.0 to 1.0>
}}

EXTRACTED VALUE FORMATS
-----------------------
- For numeric requirements (turnover, experience, warranty):
  {{"amount": <float>, "unit": "<str>"}}
- For spec requirements:
  {{"amount": <float|null>, "unit": "<str|null>", "text_value": "<str|null>"}}
- For date requirements:
  {{"date": "<YYYY-MM-DD|null>", "days": <int|null>}}
- For boolean / certification requirements:
  {{"present": true, "certificate_name": "<name>", "valid_until": "<YYYY-MM-DD|null>"}}
- For classification requirements:
  {{"class": "<Class I | Class II | Class III>", "local_content_percent": <float|null>}}

RULES
-----
1. ONLY extract evidence directly stated in the documents. Do NOT invent quotes or values.
2. If the vendor documents do not contain any information addressing this requirement, set "found": false, "file": null, "page": null, "quote": null, "extracted_value": null, and populate "search_terms" with the terms checked.
3. The quote MUST be exact and verbatim from the text of that file and page.
"""

EVIDENCE_EXTRACTION_USER = """\
VENDOR DOCUMENTS:
{vendor_documents_text}

Locate the evidence and extract the value for the requirement now.
"""


def build_evidence_extraction_prompt(
    requirement_info: dict[str, Any],
    vendor_documents_text: str,
) -> str:
    """Assemble prompt for locating requirement evidence in vendor documents."""
    system = EVIDENCE_EXTRACTION_SYSTEM.format(
        category=requirement_info.get("category", ""),
        description=requirement_info.get("description", ""),
        requirement_type=requirement_info.get("requirement_type", ""),
        operator=requirement_info.get("operator", ""),
        target_value=json.dumps(requirement_info.get("value", {})),
        unit=requirement_info.get("unit", "") or "",
    )
    user = EVIDENCE_EXTRACTION_USER.format(
        vendor_documents_text=vendor_documents_text,
    )
    return f"{system}\n\n{user}"


CONTRADICTION_DETECTION_SYSTEM = """\
You are a forensic document examiner detecting factual contradictions across multiple vendor bid documents.
Compare the documents submitted by vendor '{vendor_name}'.
Look for conflicting claims such as:
- Different annual turnover or revenue figures across documents
- Different employee counts
- Conflicting years of incorporation or experience
- Inconsistent OEM authorization claims or company details

OUTPUT FORMAT
-------------
Return a JSON object matching this schema:
{{
  "contradictions": [
    {{
      "field": "<canonical field name, e.g. 'annual_turnover', 'employee_count', 'years_in_business'>",
      "doc_a_filename": "<filename of first document>",
      "doc_a_value": "<claim or figure in first document>",
      "doc_b_filename": "<filename of second document>",
      "doc_b_value": "<contradictory claim or figure in second document>",
      "description": "<concise explanation of why these two claims contradict each other>"
    }}
  ]
}}

If there are no contradictions, return {{"contradictions": []}}.
"""

CONTRADICTION_DETECTION_USER = """\
VENDOR DOCUMENTS SUBMITTED BY {vendor_name}:
{vendor_documents_text}

Identify any contradictions across these documents now.
"""


def build_contradiction_detection_prompt(
    vendor_name: str,
    vendor_documents_text: str,
) -> str:
    """Assemble prompt for detecting cross-document contradictions."""
    system = CONTRADICTION_DETECTION_SYSTEM.format(vendor_name=vendor_name)
    user = CONTRADICTION_DETECTION_USER.format(
        vendor_name=vendor_name,
        vendor_documents_text=vendor_documents_text,
    )
    return f"{system}\n\n{user}"

