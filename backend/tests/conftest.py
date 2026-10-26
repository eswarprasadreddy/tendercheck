import json
import pytest
import pytest_asyncio
from pathlib import Path
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.main import app
from app.llm.client import GeminiClient
from tests.sample_tender_generator import generate_sample_it_hardware_tender


@pytest.fixture(scope="session")
def sample_pdf_path(tmp_path_factory) -> Path:
    tmp_dir = tmp_path_factory.mktemp("tenders")
    pdf_path = tmp_dir / "sample_laptop_tender.pdf"
    generate_sample_it_hardware_tender(pdf_path)
    return pdf_path


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_extracted_requirements_json() -> str:
    """Pre-canned valid LLM response with 10 IT hardware requirements."""
    payload = {
        "requirements": [
            {
                "category": "financial",
                "description": "Average Annual Turnover of bidder in last 3 financial years must be >= INR 1.50 Crore",
                "requirement_type": "numeric",
                "operator": ">=",
                "value": {"amount": 15000000.0, "unit": "INR"},
                "unit": "INR",
                "source_page": 1,
                "source_quote": "The average annual turnover of the bidder during the last three financial years must be at least INR 1.50 Crore",
                "is_mandatory": True,
                "llm_confidence": 0.98,
                "sector_key": "annual_turnover"
            },
            {
                "category": "experience",
                "description": "Bidder must have minimum 3 years experience in supply/maintenance of IT hardware to Govt/PSU",
                "requirement_type": "numeric",
                "operator": ">=",
                "value": {"amount": 3.0, "unit": "years"},
                "unit": "years",
                "source_page": 1,
                "source_quote": "The bidder must have at least 3 years of experience in the supply and maintenance of IT hardware",
                "is_mandatory": True,
                "llm_confidence": 0.95,
                "sector_key": "years_in_business"
            },
            {
                "category": "experience",
                "description": "Bidder must have completed at least 2 similar orders for laptops in preceding 3 years",
                "requirement_type": "numeric",
                "operator": ">=",
                "value": {"amount": 2.0, "unit": "orders"},
                "unit": "orders",
                "source_page": 1,
                "source_quote": "The bidder must have completed at least 2 similar orders for supply of laptops or computing equipment in the preceding 3 years",
                "is_mandatory": True,
                "llm_confidence": 0.94,
                "sector_key": "past_orders_count"
            },
            {
                "category": "technical_spec",
                "description": "Laptop must have minimum 16 GB DDR4/DDR5 RAM",
                "requirement_type": "spec",
                "operator": ">=",
                "value": {"amount": 16.0, "unit": "GB"},
                "unit": "GB",
                "source_page": 2,
                "source_quote": "Minimum 16 GB DDR4/DDR5 3200MHz RAM, upgradable to at least 32 GB.",
                "is_mandatory": True,
                "llm_confidence": 0.99,
                "sector_key": "ram_gb"
            },
            {
                "category": "technical_spec",
                "description": "Laptop must have minimum 512 GB M.2 NVMe PCIe SSD storage",
                "requirement_type": "spec",
                "operator": ">=",
                "value": {"amount": 512.0, "unit": "GB"},
                "unit": "GB",
                "source_page": 2,
                "source_quote": "Minimum 512 GB M.2 NVMe PCIe Gen 4 SSD storage.",
                "is_mandatory": True,
                "llm_confidence": 0.99,
                "sector_key": "ssd_gb"
            },
            {
                "category": "technical_spec",
                "description": "Processor must be Intel Core i7 13th Gen or higher",
                "requirement_type": "spec",
                "operator": "==",
                "value": {"text_value": "Intel Core i7 13th Generation or equivalent 10-core/12-core processor"},
                "unit": None,
                "source_page": 2,
                "source_quote": "Intel Core i7 13th Generation or equivalent 10-core/12-core processor (min 2.4 GHz base).",
                "is_mandatory": True,
                "llm_confidence": 0.96,
                "sector_key": "processor"
            },
            {
                "category": "technical_spec",
                "description": "Display size must be minimum 14.0 inch Full HD IPS display",
                "requirement_type": "spec",
                "operator": ">=",
                "value": {"amount": 14.0, "unit": "inches"},
                "unit": "inches",
                "source_page": 2,
                "source_quote": "Minimum 14.0 inch Full HD (1920 x 1080) Anti-Glare IPS display with 250 nits brightness.",
                "is_mandatory": True,
                "llm_confidence": 0.98,
                "sector_key": "display_inches"
            },
            {
                "category": "delivery",
                "description": "Comprehensive on-site OEM warranty for minimum 3 years",
                "requirement_type": "numeric",
                "operator": ">=",
                "value": {"amount": 3.0, "unit": "years"},
                "unit": "years",
                "source_page": 2,
                "source_quote": "Minimum 3 years comprehensive on-site OEM warranty including battery and power adapter.",
                "is_mandatory": True,
                "llm_confidence": 0.97,
                "sector_key": "warranty_years"
            },
            {
                "category": "certification",
                "description": "OEM and Bidder must have valid ISO 9001:2015 certification",
                "requirement_type": "certification",
                "operator": "exists",
                "value": {"certificate_name": "ISO 9001:2015", "required": True},
                "unit": None,
                "source_page": 3,
                "source_quote": "The OEM and the Bidder must possess a valid ISO 9001:2015 quality certificate.",
                "is_mandatory": True,
                "llm_confidence": 0.99,
                "sector_key": "iso_9001"
            },
            {
                "category": "certification",
                "description": "Quoted laptop model must have valid BIS Registration under CRS scheme",
                "requirement_type": "certification",
                "operator": "exists",
                "value": {"certificate_name": "BIS Registration", "required": True},
                "unit": None,
                "source_page": 3,
                "source_quote": "The quoted laptop model must have valid BIS Registration under the CRS scheme of MEITY (IS 13252).",
                "is_mandatory": True,
                "llm_confidence": 0.99,
                "sector_key": "bis_registration"
            },
            {
                "category": "certification",
                "description": "Non-OEM bidder must submit OEM Authorization Letter (MAF) specifically for this bid",
                "requirement_type": "certification",
                "operator": "exists",
                "value": {"certificate_name": "OEM Authorization Letter", "required": True},
                "unit": None,
                "source_page": 3,
                "source_quote": "Bidders who are not OEMs must submit an authentic OEM Authorization Letter (MAF) issued specifically for Bid GEM/2026/B/8821941.",
                "is_mandatory": True,
                "llm_confidence": 0.97,
                "sector_key": "oem_authorization"
            },
            {
                "category": "compliance",
                "description": "Make in India Class I (>=50%) or Class II (>=20%) local supplier",
                "requirement_type": "classification",
                "operator": "exists",
                "value": {"field_name": "make_in_india_class", "allowed_classes": ["Class I", "Class II"]},
                "unit": None,
                "source_page": 3,
                "source_quote": "Purchase preference will be given to Class I Local Suppliers (local content >= 50%) and Class II Local Suppliers (local content >= 20%) under PPP-MII policy.",
                "is_mandatory": True,
                "llm_confidence": 0.95,
                "sector_key": "make_in_india"
            },
            {
                "category": "delivery",
                "description": "Bid validity must be minimum 90 days from bid closing date",
                "requirement_type": "date",
                "operator": ">=",
                "value": {"days": 90},
                "unit": "days",
                "source_page": 3,
                "source_quote": "The quoted rates and bid shall remain valid for a minimum of 90 days from the bid submission closing date.",
                "is_mandatory": True,
                "llm_confidence": 0.96,
                "sector_key": "bid_validity"
            }
        ]
    }
    return json.dumps(payload)
