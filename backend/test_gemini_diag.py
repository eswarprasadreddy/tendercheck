import asyncio
from app.services.matching_engine import MatchingEngine
from app.models.requirement import Requirement
from app.models.vendor_document import VendorDocument
from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select

async def main():
    engine = create_async_engine(settings.async_database_url)
    async with engine.connect() as conn:
        # Load requirements
        res = await conn.execute(select(Requirement).order_by(Requirement.source_page.asc(), Requirement.created_at.asc()))
        reqs = list(res.fetchall())
        print(f"Total reqs: {len(reqs)}")

    matcher = MatchingEngine()
    async with engine.connect() as conn:
        res = await conn.execute(select(VendorDocument).where(VendorDocument.vendor_name.like('%Vendor A%')))
        docs = list(res.fetchall())

    corpus = matcher.format_vendor_corpus(docs)
    print("Corpus length:", len(corpus))

    for i, req in enumerate(reqs):
        print(f"\n--- Checking Req {i+1}: {req.description[:40]} (key: {req.sector_key}) ---")
        try:
            ev = matcher.extract_evidence_with_llm(req, corpus)
            print(f"   Result found={ev.found}, file={ev.file}, quote={ev.quote[:50] if ev.quote else None}")
        except Exception as e:
            print(f"   EXCEPTION: {type(e)}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
