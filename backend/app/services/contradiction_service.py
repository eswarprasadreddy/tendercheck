"""
Contradiction detection service.

Detects factual cross-document contradictions (e.g. turnover or employee counts)
across vendor documents and records them in the contradictions table.
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import GeminiClient, get_gemini_client
from app.llm.prompts import build_contradiction_detection_prompt
from app.llm.validators import validate_llm_json
from app.models.contradiction import Contradiction
from app.models.vendor_document import VendorDocument
from app.schemas.contradiction import ContradictionList

logger = logging.getLogger(__name__)


def _extract_turnover_mentions(text: str) -> Optional[str]:
    """Find explicit turnover statement in text if present."""
    match = re.search(
        r"(?:turnover|revenue)[^\n\.\,]{0,40}?(?:inr|rs\.?|₹)?\s*([\d\.]+\s*(?:crore|cr|lakh|lac|inr|rs)?)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(0).strip()
    return None


def _extract_employee_count_mentions(text: str) -> Optional[str]:
    """Find explicit employee count statement in text if present."""
    match = re.search(
        r"(\d+)\s*(?:full[-\s]time\s*)?(?:employees|workforce|staff|personnel)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(0).strip()
    return None


def detect_heuristic_contradictions(
    docs: list[VendorDocument],
) -> list[dict]:
    """
    Deterministically scan document texts for conflicting profile values
    like employee counts and turnover figures.
    """
    contradictions: list[dict] = []
    if len(docs) < 2:
        return contradictions

    # Check pairs of documents
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            doc_a = docs[i]
            doc_b = docs[j]
            text_a = doc_a.raw_text or ""
            text_b = doc_b.raw_text or ""

            # 1. Turnover comparison
            turn_a = _extract_turnover_mentions(text_a)
            turn_b = _extract_turnover_mentions(text_b)
            if turn_a and turn_b and turn_a.lower() != turn_b.lower():
                # Check if numbers differ
                nums_a = re.findall(r"\d+\.?\d*", turn_a)
                nums_b = re.findall(r"\d+\.?\d*", turn_b)
                if nums_a and nums_b and nums_a[0] != nums_b[0]:
                    contradictions.append({
                        "field": "annual_turnover",
                        "doc_a": doc_a,
                        "doc_a_value": turn_a,
                        "doc_b": doc_b,
                        "doc_b_value": turn_b,
                        "description": f"Conflicting annual turnover figures found: '{turn_a}' in {doc_a.original_filename} vs '{turn_b}' in {doc_b.original_filename}.",
                    })

            # 2. Employee count comparison
            emp_a = _extract_employee_count_mentions(text_a)
            emp_b = _extract_employee_count_mentions(text_b)
            if emp_a and emp_b and emp_a.lower() != emp_b.lower():
                nums_a = re.findall(r"\d+", emp_a)
                nums_b = re.findall(r"\d+", emp_b)
                if nums_a and nums_b and nums_a[0] != nums_b[0]:
                    contradictions.append({
                        "field": "employee_count",
                        "doc_a": doc_a,
                        "doc_a_value": emp_a,
                        "doc_b": doc_b,
                        "doc_b_value": emp_b,
                        "description": f"Conflicting employee counts found: '{emp_a}' in {doc_a.original_filename} vs '{emp_b}' in {doc_b.original_filename}.",
                    })

    return contradictions


class ContradictionDetector:
    def __init__(self, client: Optional[GeminiClient] = None) -> None:
        self._client = client

    def _get_client(self) -> GeminiClient:
        if self._client is None:
            self._client = get_gemini_client()
        return self._client

    async def detect_and_save(
        self,
        db: AsyncSession,
        tender_id: uuid.UUID,
        vendor_name: str,
        vendor_docs: list[VendorDocument],
    ) -> list[Contradiction]:
        """
        Detect contradictions across vendor documents using heuristics and Gemini,
        and persist them to the database.
        """
        if len(vendor_docs) < 2:
            return []

        doc_by_filename = {doc.original_filename: doc for doc in vendor_docs}

        # Clear existing contradictions for this vendor/tender
        existing = await db.scalars(
            select(Contradiction).where(
                Contradiction.tender_id == tender_id,
                Contradiction.vendor_name == vendor_name,
            )
        )
        for c in existing:
            await db.delete(c)
        await db.flush()

        results: list[Contradiction] = []

        # 1. Deterministic heuristic check
        heuristic_matches = detect_heuristic_contradictions(vendor_docs)
        for h in heuristic_matches:
            c = Contradiction(
                tender_id=tender_id,
                vendor_name=vendor_name,
                field=h["field"],
                doc_a_id=h["doc_a"].id,
                doc_a_filename=h["doc_a"].original_filename,
                doc_a_value=h["doc_a_value"],
                doc_b_id=h["doc_b"].id,
                doc_b_filename=h["doc_b"].original_filename,
                doc_b_value=h["doc_b_value"],
                description=h["description"],
            )
            db.add(c)
            results.append(c)

        # 2. LLM cross-document contradiction detection (if client is configured)
        try:
            client = self._get_client()
            combined_text = "\n\n".join(
                f"=== DOCUMENT: {doc.original_filename} ===\n{doc.raw_text or ''}"
                for doc in vendor_docs
            )
            prompt = build_contradiction_detection_prompt(vendor_name, combined_text)
            raw = client.generate_json(prompt)
            parsed: ContradictionList = validate_llm_json(
                raw=raw,
                model_cls=ContradictionList,
                client=client,
                original_prompt=prompt,
            )

            for item in parsed.contradictions:
                # Avoid duplicate if already caught by heuristics
                if any(r.field == item.field for r in results):
                    continue

                doc_a = doc_by_filename.get(item.doc_a_filename) or vendor_docs[0]
                doc_b = doc_by_filename.get(item.doc_b_filename) or vendor_docs[1]

                c = Contradiction(
                    tender_id=tender_id,
                    vendor_name=vendor_name,
                    field=item.field,
                    doc_a_id=doc_a.id,
                    doc_a_filename=doc_a.original_filename,
                    doc_a_value=item.doc_a_value,
                    doc_b_id=doc_b.id,
                    doc_b_filename=doc_b.original_filename,
                    doc_b_value=item.doc_b_value,
                    description=item.description,
                )
                db.add(c)
                results.append(c)
        except Exception as exc:
            logger.info("LLM contradiction detection skipped or errored: %s", exc)

        await db.commit()
        for r in results:
            await db.refresh(r)
        return results
