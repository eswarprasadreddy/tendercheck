"""
Requirement extraction service.

Flow
----
1. Load the sector config JSON (cached per sector_id).
2. Build the extraction prompt via ``llm.prompts``.
3. Call Gemini via ``GeminiClient.generate_json()``.
4. Validate + retry via ``llm.validators.validate_llm_json()``.
5. Return a list of ``LLMRequirement`` objects ready for DB persistence.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings
from app.llm.client import GeminiClient, get_gemini_client
from app.llm.prompts import build_requirement_extraction_prompt
from app.llm.validators import LLMOutputError, validate_llm_json
from app.schemas.requirement import LLMRequirement, LLMRequirementList

logger = logging.getLogger(__name__)

SECTORS_DIR = Path(__file__).parent.parent / "sectors"


@lru_cache(maxsize=16)
def load_sector_config(sector_id: str) -> dict[str, Any]:
    """Load and cache sector JSON config.  Unknown sectors fall back to an empty dict."""
    config_path = SECTORS_DIR / f"{sector_id}.json"
    if not config_path.exists():
        logger.warning("Sector config not found for '%s' — using empty config.", sector_id)
        return {"sector_id": sector_id, "sector_name": sector_id.replace("_", " ").title()}
    with config_path.open(encoding="utf-8") as fh:
        return json.load(fh)


class RequirementParser:
    """
    Extracts structured eligibility requirements from tender text using Gemini.

    Parameters
    ----------
    client:     GeminiClient instance.  Pass explicitly in tests (makes mocking trivial).
    sector_id:  Sector identifier — must match a file under app/sectors/.
    """

    def __init__(
        self,
        client: GeminiClient | None = None,
        sector_id: str | None = None,
    ) -> None:
        self._client = client  # lazy — resolved in extract()
        self._sector_id = sector_id or settings.sector

    def _get_client(self) -> GeminiClient:
        if self._client is None:
            self._client = get_gemini_client()
        return self._client

    def extract(
        self,
        tender_text: str,
        page_count: int = 1,
    ) -> list[LLMRequirement]:
        """
        Extract requirements from *tender_text*.

        Parameters
        ----------
        tender_text:  Full concatenated text from ``PDFExtractionResult.full_text``.
        page_count:   Number of pages in the document (used in prompt).

        Returns
        -------
        List of validated ``LLMRequirement`` objects.

        Raises
        ------
        LLMOutputError  If Gemini returns invalid JSON after 2 attempts.
        """
        sector_config = load_sector_config(self._sector_id)
        client = self._get_client()

        # Truncate to stay within context limit
        truncated = tender_text[: settings.llm_context_limit]
        if len(tender_text) > settings.llm_context_limit:
            logger.warning(
                "Tender text truncated from %d to %d chars for LLM.",
                len(tender_text), settings.llm_context_limit,
            )

        prompt = build_requirement_extraction_prompt(
            tender_text=truncated,
            page_count=page_count,
            sector_config=sector_config,
        )

        logger.info("Starting requirement extraction — sector=%s", self._sector_id)
        raw = client.generate_json(prompt)

        result: LLMRequirementList = validate_llm_json(
            raw=raw,
            model_cls=LLMRequirementList,
            client=client,
            original_prompt=prompt,
        )

        logger.info("Extracted %d requirements.", len(result.requirements))
        return result.requirements
