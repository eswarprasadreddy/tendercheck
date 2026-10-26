"""
JSON forcing + Pydantic validation layer for all LLM outputs.

Strategy
--------
1. Ask Gemini with ``response_mime_type="application/json"`` (SDK-level JSON mode).
2. Attempt ``model.model_validate_json(raw)``.
3. On ``ValidationError``, log the error and retry ONCE with an explicit repair
   prompt asking the model to fix the JSON.
4. If the second attempt also fails, raise ``LLMOutputError`` so the caller
   can mark the tender as FAILED and surface a clear error to the operator.

This approach is deterministic: the validation retry never goes more than two
LLM calls per request, keeping latency and cost predictable.
"""
from __future__ import annotations

import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.client import GeminiClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

JSON_REPAIR_SUFFIX = """

---
The JSON you returned failed schema validation with this error:
{error}

Please return ONLY the corrected JSON that matches the required schema.
Do NOT include any explanation or markdown fencing.
"""


class LLMOutputError(Exception):
    """Raised when the LLM fails to produce valid JSON after retries."""

    def __init__(self, message: str, raw_response: str = "") -> None:
        super().__init__(message)
        self.raw_response = raw_response


def extract_json_block(raw: str) -> str:
    """
    Strip markdown code fences if the model returned them despite JSON mode.
    e.g. ```json\n{...}\n```  →  {...}
    """
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        # Drop first line (```json) and last line (```)
        inner_lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        raw = "\n".join(inner_lines)
    return raw


def validate_llm_json(
    raw: str,
    model_cls: type[T],
    client: GeminiClient,
    original_prompt: str,
) -> T:
    """
    Parse *raw* JSON and validate against *model_cls*.

    Retries once with a repair prompt on ``ValidationError`` or ``json.JSONDecodeError``.

    Parameters
    ----------
    raw:             Raw string from the LLM.
    model_cls:       Pydantic model to validate against.
    client:          GeminiClient used for the repair retry.
    original_prompt: The original prompt (prepended to the repair prompt).
    """
    # Attempt 1
    cleaned = extract_json_block(raw)
    try:
        return model_cls.model_validate_json(cleaned)
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        error_summary = str(exc)[:800]
        logger.warning("LLM JSON validation failed (attempt 1): %s", error_summary)

    # Attempt 2 — ask the model to repair its own output
    repair_prompt = original_prompt + JSON_REPAIR_SUFFIX.format(
        error=error_summary
    )
    raw2 = client.generate_json(repair_prompt)
    cleaned2 = extract_json_block(raw2)

    try:
        return model_cls.model_validate_json(cleaned2)
    except (ValidationError, json.JSONDecodeError, ValueError) as exc2:
        logger.error("LLM JSON validation failed (attempt 2): %s", str(exc2)[:800])
        raise LLMOutputError(
            f"LLM returned invalid JSON after 2 attempts: {exc2}",
            raw_response=raw2,
        ) from exc2
