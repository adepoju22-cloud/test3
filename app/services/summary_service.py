"""
Summary service: transforms raw database aggregates into the response
shape expected by the API and the PDF/CSV report generators.
"""

from sqlalchemy.orm import Session

from app.database import crud
from app.models.schemas import SeverityBreakdown, SummaryResponse


def build_summary(db: Session) -> SummaryResponse:
    """Compute and return the compliance summary for the latest scan."""
    raw = crud.get_summary(db)
    return SummaryResponse(
        total_findings=raw["total_findings"],
        passed=raw["passed"],
        failed=raw["failed"],
        compliance_percentage=raw["compliance_percentage"],
        severity_breakdown=SeverityBreakdown(**raw["severity_breakdown"]),
        findings_by_framework=raw["findings_by_framework"],
        top_violated_rules=raw["top_violated_rules"],
    )
