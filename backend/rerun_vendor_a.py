import asyncio
from app.database import get_engine, init_db, _session_factory
from app.config import settings
from app.services.matching_engine import MatchingEngine
from app.services.report_service import generate_vendor_report
from sqlalchemy import select
from app.models.tender import Tender
from app.models.report import Report
from app.models.match import Match

async def main():
    import app.database as app_db
    app_db.init_db(settings.async_database_url)
    async with app_db._session_factory() as session:
        tender = await session.scalar(select(Tender).where(Tender.reference_number == "GEM/2026/B/8821941"))
        if not tender:
            print("Tender not found")
            return
        
        for vendor_name in ["Vendor A (Apex Tech Solutions Pvt Ltd)", "Vendor B (Nexura Hardware Systems Ltd)"]:
            print(f"\n--- Rerunning matching for {vendor_name} ---")
            engine = MatchingEngine()
            matches = await engine.run_matching(db=session, tender_id=tender.id, vendor_name=vendor_name)
            report = await generate_vendor_report(db=session, tender_id=tender.id, vendor_name=vendor_name)
            print(f"Pass: {report.pass_count} | Fail: {report.fail_count} | Missing: {report.missing_count} | Mismatch: {report.mismatch_count} | Contradictions: {report.contradiction_count}")
            print(f"Overall Verdict: {report.overall_verdict}")
        
        for i, m in enumerate(matches):
            print(f"{i+1}. [{m.verdict}] req_id={m.requirement_id} | File: {m.evidence_file} | Reason: {m.verdict_reason[:60]}")

if __name__ == "__main__":
    asyncio.run(main())
