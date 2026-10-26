from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    # Optional so tests can run without a real key; validated at LLM-client init time.
    gemini_api_key: Optional[str] = None
    model_name: str = "gemini-2.0-flash"

    # Database
    database_url: str = (
        "postgresql+asyncpg://tendercheck:tendercheck@localhost:5432/tendercheck"
    )

    # File storage
    upload_dir: Path = Path("uploads")

    # Sector config directory (relative to app package root)
    sector: str = "it_hardware"

    # PDF extraction
    # Pages with fewer chars than this threshold are re-processed with OCR
    ocr_threshold: int = 50

    # Max characters of tender text forwarded to the LLM
    llm_context_limit: int = 120_000

    # ------------------------------------------------------------------ #
    # Derived helpers                                                       #
    # ------------------------------------------------------------------ #

    @property
    def async_database_url(self) -> str:
        """Guarantee the URL uses the asyncpg driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """psycopg2-based URL for Alembic (which is sync)."""
        return (
            self.async_database_url
            .replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
