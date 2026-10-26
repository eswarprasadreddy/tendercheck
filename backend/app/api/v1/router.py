from fastapi import APIRouter

from app.api.v1 import matching, reports, tenders, vendor_documents

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(tenders.router)
api_router.include_router(vendor_documents.router)
api_router.include_router(matching.router)
api_router.include_router(reports.router)
