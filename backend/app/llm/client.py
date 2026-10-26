"""
Thin wrapper around the google-genai SDK.

Why a wrapper?
--------------
* Centralises API-key validation (fails loudly at client construction, not at
  the first request).
* Lets tests mock ``GeminiClient`` without patching deep SDK internals.
* Provides a single ``generate_json`` method with automatic JSON mode enabled.
"""
from __future__ import annotations

import logging

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Synchronous (thread-safe) Gemini client for JSON generation."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is not set.  "
                "Add it to your .env file or environment variables."
            )
        self._client = genai.Client(api_key=key)
        self._model = model_name or settings.model_name

    def generate_json(self, prompt: str) -> str:
        """
        Send *prompt* to Gemini and return the raw JSON string.

        The SDK is configured with ``response_mime_type="application/json"``
        so the model is constrained to return valid JSON.  We still validate
        the structure with Pydantic in the calling layer.
        """
        logger.debug("Calling Gemini model=%s prompt_len=%d", self._model, len(prompt))

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,   # low temp = deterministic, less hallucination
                max_output_tokens=8192,
            ),
        )

        raw = response.text
        logger.debug("Gemini response len=%d", len(raw) if raw else 0)
        return raw or ""


# Module-level singleton — constructed lazily so tests can import this module
# without a real API key.
_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
