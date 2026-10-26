import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base
from app.models.tender import Tender, TenderStatus
from app.models.requirement import Requirement, RequirementType, RequirementCategory


@pytest.mark.asyncio
async def test_models_create_in_sqlite():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        tender = Tender(
            title="Laptop Procurement GeM Tender",
            reference_number="GEM/2026/B/9999",
            pdf_path="/tmp/test.pdf",
            status=TenderStatus.UPLOADED.value,
        )
        session.add(tender)
        await session.commit()
        await session.refresh(tender)

        assert tender.id is not None
        assert tender.status == "uploaded"

        req = Requirement(
            tender_id=tender.id,
            category=RequirementCategory.TECHNICAL_SPEC.value,
            description="RAM must be at least 16 GB",
            requirement_type=RequirementType.SPEC.value,
            operator=">=",
            value={"amount": 16, "unit": "GB"},
            unit="GB",
            source_page=1,
            source_quote="The laptop shall have minimum 16 GB RAM",
            is_mandatory=True,
            sector_key="ram_gb",
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)

        assert req.id is not None
        assert req.tender_id == tender.id
        assert req.operator == ">="

    await engine.dispose()
