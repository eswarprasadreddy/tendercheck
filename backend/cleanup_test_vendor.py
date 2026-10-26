import asyncio
from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def cleanup():
    engine = create_async_engine(settings.async_database_url)
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM matches WHERE vendor_document_id IN (SELECT id FROM vendor_documents WHERE vendor_name LIKE '%Consortium%' OR vendor_name LIKE '%[Test%')"))
        await conn.execute(text("DELETE FROM vendor_documents WHERE vendor_name LIKE '%Consortium%' OR vendor_name LIKE '%[Test%'"))
        await conn.execute(text("DELETE FROM reports WHERE vendor_name LIKE '%Consortium%' OR vendor_name LIKE '%[Test%'"))
        await conn.execute(text("DELETE FROM contradictions WHERE vendor_name LIKE '%Consortium%' OR vendor_name LIKE '%[Test%'"))
    print("Cleaned test vendors from DB")

if __name__ == "__main__":
    asyncio.run(cleanup())
