"""
Scan orchestration service.

Ties together the loader (resources + rules), the scanning engine, and the
database layer. This is the single entry point used by both the FastAPI
POST /scan endpoint and any CLI / scheduled job.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.database import crud
from app.models.schemas import ScanResponse
from app.scanner.engine import scan
from app.scanner.loader import load_resources, load_rules
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_scan(db: Session, replace_existing: bool = True) -> ScanResponse:
    """
    Execute a full compliance scan and persist the results.

    Args:
        db: Active SQLAlchemy session.
        replace_existing: If True, clears prior results before storing the
            new scan (keeps the dashboard showing only the latest run).

    Returns:
        A ScanResponse summarizing what happened.
    """
    logger.info("Starting compliance scan...")
    resources = load_resources()
    rules = load_rules()

    findings = scan(resources, rules)

    if replace_existing:
        crud.clear_results(db)

    inserted = crud.bulk_insert_findings(db, findings)
    passed = sum(1 for f in findings if f.status.value == "PASS")
    failed = len(findings) - passed

    response = ScanResponse(
        message="Scan completed successfully",
        resources_scanned=len(resources),
        rules_evaluated=len(rules),
        findings_generated=inserted,
        passed=passed,
        failed=failed,
        scan_time=datetime.utcnow(),
    )
    logger.info(
        "Scan persisted: %d findings (%d PASS / %d FAIL)", inserted, passed, failed
    )
    return response
