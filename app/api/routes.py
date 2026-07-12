"""
REST API route definitions.

Endpoints (per FEATURE 6 of the spec):
    GET  /results
    GET  /summary
    GET  /critical
    GET  /failed
    POST /scan
    GET  /resources
    GET  /rules
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import crud
from app.database.db import get_db
from app.models.schemas import ComplianceResultOut, Resource, Rule, ScanResponse, SummaryResponse
from app.reports.csv_report import generate_csv_report
from app.reports.pdf_report import generate_pdf_report
from app.scanner.loader import load_resources, load_rules
from app.services.scan_service import run_scan
from app.services.summary_service import build_summary
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/scan", response_model=ScanResponse, tags=["Scanner"])
def trigger_scan(db: Session = Depends(get_db)) -> ScanResponse:
    """Run a full compliance scan and persist the results."""
    try:
        return run_scan(db)
    except Exception as exc:
        logger.exception("Scan failed")
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}") from exc


@router.get("/results", response_model=list[ComplianceResultOut], tags=["Results"])
def get_results(
    status: Optional[str] = Query(None, description="Filter by PASS or FAIL"),
    severity: Optional[str] = Query(
        None, description="Filter by Critical, High, Medium, or Low"
    ),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[ComplianceResultOut]:
    """Return stored compliance results, optionally filtered."""
    return crud.get_all_results(db, status, severity, resource_type, limit, offset)


@router.get("/summary", response_model=SummaryResponse, tags=["Results"])
def get_summary(db: Session = Depends(get_db)) -> SummaryResponse:
    """Return aggregate compliance statistics for the latest scan."""
    return build_summary(db)


@router.get("/critical", response_model=list[ComplianceResultOut], tags=["Results"])
def get_critical(db: Session = Depends(get_db)) -> list[ComplianceResultOut]:
    """Return all failed findings with Critical severity."""
    return crud.get_critical_results(db)


@router.get("/failed", response_model=list[ComplianceResultOut], tags=["Results"])
def get_failed(db: Session = Depends(get_db)) -> list[ComplianceResultOut]:
    """Return all failed findings, ordered by severity."""
    return crud.get_failed_results(db)


@router.get("/resources", response_model=list[Resource], tags=["Inventory"])
def get_resources() -> list[Resource]:
    """Return the raw resource inventory loaded from resources.json."""
    return load_resources()


@router.get("/rules", response_model=list[Rule], tags=["Inventory"])
def get_rules() -> list[Rule]:
    """Return every compliance rule loaded from the rules directory."""
    return load_rules()


@router.get("/reports/pdf", tags=["Reports"])
def download_pdf_report(db: Session = Depends(get_db)) -> FileResponse:
    """Generate and download a PDF compliance report."""
    path = generate_pdf_report(db)
    return FileResponse(
        path=str(path), media_type="application/pdf", filename=path.name
    )


@router.get("/reports/csv", tags=["Reports"])
def download_csv_report(db: Session = Depends(get_db)) -> FileResponse:
    """Generate and download a CSV compliance report."""
    path = generate_csv_report(db)
    return FileResponse(path=str(path), media_type="text/csv", filename=path.name)
