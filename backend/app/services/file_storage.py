"""
File storage service.

Abstracts local disk storage behind a simple interface so it can be swapped
for S3 (or GCS) later without touching the API layer.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles

from app.config import settings


def _upload_root() -> Path:
    root = settings.upload_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def tender_dir(tender_id: uuid.UUID) -> Path:
    p = _upload_root() / "tenders" / str(tender_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def vendor_dir(tender_id: uuid.UUID, vendor_name: str) -> Path:
    safe = vendor_name.replace(" ", "_").lower()
    p = _upload_root() / "vendors" / str(tender_id) / safe
    p.mkdir(parents=True, exist_ok=True)
    return p


async def save_upload(dest: Path, data: bytes) -> None:
    """Write *data* to *dest* asynchronously."""
    async with aiofiles.open(dest, "wb") as fh:
        await fh.write(data)
