"""
Tender endpoints.

POST /api/v1/tenders/upload
    - Accept multipart PDF upload + title + reference_number form fields
    - Save file to disk
    - Create tender row (status=uploaded)
    - Schedule async background task: extract text + parse requirements
    - Return 202 with tender_id

GET /api/v1/tenders/{tender_id}
    - Return tender metadata + current status

GET /api/v1/tenders/{tender_id}/requirements
    - Return all parsed requirements for the tender

PATCH /api/v1/tenders/{tender_id}/requirements/{req_id}
    - Allow officer to override a requirement's value/description
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.requirement import Requirement
from app.models.tender import Tender, TenderStatus
from app.schemas.requirement import (
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
)
from app.schemas.tender import TenderResponse
from app.services.file_storage import save_upload, tender_dir

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenders", tags=["tenders"])


# ------------------------------------------------------------------ #
# Background task: extract + parse                                      #
# ------------------------------------------------------------------ #


async def _process_tender(
    tender_id: uuid.UUID,
    pdf_path: Path,
    session: AsyncSession | None = None,
    parser: RequirementParser | None = None,
) -> None:
    """
    Extract text with PyMuPDF / OCR and parse requirements with Gemini.
    Can be run in background tasks or called directly.
    """
    from app.database import _session_factory
    from app.llm.validators import LLMOutputError
    from app.models.requirement import Requirement
    from app.services.pdf_extractor import extract_pdf
    from app.services.requirement_parser import RequirementParser

    parser = parser or RequirementParser()

    async def _execute(sess: AsyncSession) -> None:
        # Mark as parsing
        await sess.execute(
            update(Tender)
            .where(Tender.id == tender_id)
            .values(status=TenderStatus.PARSING.value)
        )
        await sess.commit()

        try:
            # Step 1: Extract text
            result = extract_pdf(pdf_path)

            # Step 2: Parse requirements
            llm_requirements = parser.extract(
                tender_text=result.full_text,
                page_count=result.page_count,
            )

            # Step 3: Persist
            for llm_req in llm_requirements:
                req = Requirement(
                    tender_id=tender_id,
                    category=llm_req.category,
                    description=llm_req.description,
                    requirement_type=llm_req.requirement_type,
                    operator=llm_req.operator,
                    value=llm_req.value,
                    unit=llm_req.unit,
                    source_page=llm_req.source_page,
                    source_quote=llm_req.source_quote,
                    llm_confidence=llm_req.llm_confidence,
                    is_mandatory=llm_req.is_mandatory,
                    sector_key=llm_req.sector_key,
                )
                sess.add(req)

            await sess.execute(
                update(Tender)
                .where(Tender.id == tender_id)
                .values(
                    status=TenderStatus.PARSED.value,
                    raw_text=result.full_text,
                    page_count=result.page_count,
                )
            )
            await sess.commit()
            logger.info(
                "Tender %s processed: %d requirements extracted.", tender_id, len(llm_requirements)
            )

        except LLMOutputError as exc:
            logger.error("Tender %s LLM error: %s", tender_id, exc)
            await sess.execute(
                update(Tender)
                .where(Tender.id == tender_id)
                .values(status=TenderStatus.FAILED.value, error_message=str(exc))
            )
            await sess.commit()

        except Exception as exc:  # noqa: BLE001
            logger.exception("Tender %s unexpected error: %s", tender_id, exc)
            await sess.execute(
                update(Tender)
                .where(Tender.id == tender_id)
                .values(status=TenderStatus.FAILED.value, error_message=str(exc))
            )
            await sess.commit()

    if session is not None:
        await _execute(session)
    elif _session_factory is not None:
        async with _session_factory() as sess:
            await _execute(sess)
    else:
        logger.error("DB not initialised — cannot process tender %s", tender_id)


# ------------------------------------------------------------------ #
# Endpoints                                                             #
# ------------------------------------------------------------------ #


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TenderResponse,
    summary="Upload a tender PDF and trigger async requirement extraction",
)
async def upload_tender(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    title: str = Form(..., description="Tender title"),
    reference_number: str = Form(..., description="Unique tender reference / GeM bid number"),
    db: AsyncSession = Depends(get_db),
) -> TenderResponse:
    # Validate file type
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted.",
        )

    # Check for duplicate reference number
    existing = await db.scalar(
        select(Tender).where(Tender.reference_number == reference_number)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tender with reference_number '{reference_number}' already exists.",
        )

    # Create DB record first (get the UUID)
    tender = Tender(
        title=title,
        reference_number=reference_number,
        pdf_path="pending",  # updated after file save
        status=TenderStatus.UPLOADED.value,
    )
    db.add(tender)
    await db.flush()  # assigns tender.id without committing

    # Save file to disk
    dest_dir = tender_dir(tender.id)
    safe_filename = f"tender_{tender.id}.pdf"
    dest_path = dest_dir / safe_filename
    contents = await file.read()
    await save_upload(dest_path, contents)

    tender.pdf_path = str(dest_path)
    await db.commit()
    await db.refresh(tender)

    # Schedule background processing
    background_tasks.add_task(_process_tender, tender.id, dest_path)

    logger.info("Tender %s uploaded — processing queued.", tender.id)
    return TenderResponse.model_validate(tender)


@router.get(
    "",
    response_model=list[TenderResponse],
    summary="List all tenders",
)
async def list_tenders(
    db: AsyncSession = Depends(get_db),
) -> list[TenderResponse]:
    rows = await db.scalars(select(Tender).order_by(Tender.created_at.desc()))
    return [TenderResponse.model_validate(t) for t in rows]


@router.get(
    "/{tender_id}",
    response_model=TenderResponse,
    summary="Get tender metadata and current processing status",
)
async def get_tender(
    tender_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TenderResponse:
    tender = await db.get(Tender, tender_id)
    if tender is None:
        raise HTTPException(status_code=404, detail="Tender not found.")
    return TenderResponse.model_validate(tender)


@router.get(
    "/{tender_id}/requirements",
    response_model=list[RequirementResponse],
    summary="List all requirements extracted from a tender",
)
async def list_requirements(
    tender_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[RequirementResponse]:
    tender = await db.get(Tender, tender_id)
    if tender is None:
        raise HTTPException(status_code=404, detail="Tender not found.")
    if tender.status not in (TenderStatus.PARSED.value, TenderStatus.PARSING.value):
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail=f"Tender is not yet parsed (status={tender.status}).",
        )

    rows = await db.scalars(
        select(Requirement)
        .where(Requirement.tender_id == tender_id)
        .order_by(Requirement.source_page.asc(), Requirement.created_at.asc())
    )
    reqs = list(rows)
    return [RequirementResponse.model_validate(r) for r in reqs]


@router.patch(
    "/{tender_id}/requirements/{req_id}",
    response_model=RequirementResponse,
    summary="Allow officer to edit a requirement before matching",
)
async def update_requirement(
    tender_id: uuid.UUID,
    req_id: uuid.UUID,
    payload: RequirementUpdate,
    db: AsyncSession = Depends(get_db),
) -> RequirementResponse:
    req = await db.get(Requirement, req_id)
    if req is None or req.tender_id != tender_id:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(req, field, val)

    await db.commit()
    await db.refresh(req)
    return RequirementResponse.model_validate(req)


@router.delete(
    "/{tender_id}/requirements/{req_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Allow officer to delete an incorrect requirement before matching",
)
async def delete_requirement(
    tender_id: uuid.UUID,
    req_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    req = await db.get(Requirement, req_id)
    if req is None or req.tender_id != tender_id:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    await db.delete(req)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{tender_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Allow officer to manually add a requirement before matching",
)
async def create_requirement(
    tender_id: uuid.UUID,
    payload: RequirementCreate,
    db: AsyncSession = Depends(get_db),
) -> RequirementResponse:
    tender = await db.get(Tender, tender_id)
    if tender is None:
        raise HTTPException(status_code=404, detail="Tender not found.")

    req = Requirement(
        tender_id=tender_id,
        category=payload.category,
        description=payload.description,
        requirement_type=payload.requirement_type,
        operator=payload.operator,
        value=payload.value,
        unit=payload.unit,
        source_page=payload.source_page,
        source_quote=payload.source_quote,
        is_mandatory=payload.is_mandatory,
        sector_key=payload.sector_key,
        llm_confidence=1.0,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return RequirementResponse.model_validate(req)


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset all evaluation data to start a clean demo",
)
async def reset_demo_data(
    db: AsyncSession = Depends(get_db),
) -> dict:
    from sqlalchemy import text
    await db.execute(text("DELETE FROM matches"))
    await db.execute(text("DELETE FROM contradictions"))
    await db.execute(text("DELETE FROM reports"))
    await db.execute(text("DELETE FROM vendor_documents"))
    await db.execute(text("DELETE FROM requirements"))
    await db.execute(text("DELETE FROM tenders"))
    await db.commit()
    return {"status": "ok", "message": "All evaluation data and uploaded tenders reset."}


