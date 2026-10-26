"""
Import all models here so Alembic's env.py and Base.metadata are fully populated
when create_all / autogenerate runs.
"""
from app.models.tender import Tender, TenderStatus  # noqa: F401
from app.models.requirement import Requirement, RequirementType, RequirementCategory  # noqa: F401
from app.models.vendor_document import VendorDocument, VendorDocStatus  # noqa: F401
from app.models.match import Match, Verdict  # noqa: F401
from app.models.report import Report, OverallVerdict  # noqa: F401
from app.models.contradiction import Contradiction  # noqa: F401
