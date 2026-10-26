"""
TenderCheck FastAPI application entry point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN001
    """Startup: initialise DB.  Shutdown: nothing to do (engine pool closes automatically)."""
    logger.info("TenderCheck starting — sector=%s model=%s", settings.sector, settings.model_name)
    init_db(settings.async_database_url)
    yield
    logger.info("TenderCheck shutting down.")


app = FastAPI(
    title="TenderCheck API",
    description=(
        "AI-assisted compliance checker for government tender bid documents. "
        "The AI is purely advisory — a human officer must confirm all verdicts."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Direct root-level route for officer confirmation
from app.api.v1.reports import confirm_report_endpoint
app.post("/report/confirm", tags=["reports"], summary="Officer confirmation (root path)")(confirm_report_endpoint)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}

