"""
Data-access helper functions (CRUD) for compliance_results.

Keeping these queries in one module keeps the API route handlers and the
scanner service free of raw SQLAlchemy query logic, making the codebase
easier to test and extend.
"""

from collections import Counter
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import ComplianceResult
from app.models.schemas import Finding


def bulk_insert_findings(db: Session, findings: list[Finding]) -> int:
    """
    Persist a list of Finding objects as ComplianceResult rows.

    Args:
        db: Active SQLAlchemy session.
        findings: Findings produced by the scanner engine.

    Returns:
        The number of rows inserted.
    """
    rows = [
        ComplianceResult(
            resource_name=f.resource_name,
            resource_type=f.resource_type.value,
            rule_id=f.rule_id,
            rule_name=f.rule_name,
            severity=f.severity.value,
            status=f.status.value,
            framework=f.framework,
            recommendation=f.recommendation,
            scan_time=f.scan_time,
        )
        for f in findings
    ]
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)


def clear_results(db: Session) -> None:
    """Delete all existing compliance results (used before a fresh scan)."""
    db.query(ComplianceResult).delete()
    db.commit()


def get_all_results(
    db: Session,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
) -> list[ComplianceResult]:
    """Return compliance results, optionally filtered by status/severity/type."""
    query = db.query(ComplianceResult)
    if status:
        query = query.filter(ComplianceResult.status == status.upper())
    if severity:
        query = query.filter(ComplianceResult.severity == severity.capitalize())
    if resource_type:
        query = query.filter(ComplianceResult.resource_type == resource_type)
    return (
        query.order_by(ComplianceResult.scan_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_failed_results(db: Session) -> list[ComplianceResult]:
    """Return all FAIL findings."""
    return (
        db.query(ComplianceResult)
        .filter(ComplianceResult.status == "FAIL")
        .order_by(ComplianceResult.severity.asc())
        .all()
    )


def get_critical_results(db: Session) -> list[ComplianceResult]:
    """Return all FAIL findings with Critical severity."""
    return (
        db.query(ComplianceResult)
        .filter(
            ComplianceResult.status == "FAIL",
            ComplianceResult.severity == "Critical",
        )
        .all()
    )


def get_summary(db: Session) -> dict[str, Any]:
    """
    Compute aggregate compliance statistics: totals, pass/fail counts,
    compliance percentage, severity breakdown, findings by framework, and
    the most frequently violated rules.
    """
    total = db.query(func.count(ComplianceResult.id)).scalar() or 0
    passed = (
        db.query(func.count(ComplianceResult.id))
        .filter(ComplianceResult.status == "PASS")
        .scalar()
        or 0
    )
    failed = total - passed
    compliance_percentage = round((passed / total) * 100, 2) if total else 0.0

    severity_rows = (
        db.query(ComplianceResult.severity, func.count(ComplianceResult.id))
        .filter(ComplianceResult.status == "FAIL")
        .group_by(ComplianceResult.severity)
        .all()
    )
    severity_counts = {sev.lower(): count for sev, count in severity_rows}
    severity_breakdown = {
        "critical": severity_counts.get("critical", 0),
        "high": severity_counts.get("high", 0),
        "medium": severity_counts.get("medium", 0),
        "low": severity_counts.get("low", 0),
    }

    framework_rows = db.query(ComplianceResult.framework).filter(
        ComplianceResult.status == "FAIL"
    ).all()
    framework_counter: Counter = Counter()
    for (framework_str,) in framework_rows:
        for token in framework_str.split(";"):
            token = token.strip()
            if token:
                framework_counter[token.split(":")[0]] += 1

    top_rules_rows = (
        db.query(
            ComplianceResult.rule_id,
            ComplianceResult.rule_name,
            func.count(ComplianceResult.id).label("violations"),
        )
        .filter(ComplianceResult.status == "FAIL")
        .group_by(ComplianceResult.rule_id, ComplianceResult.rule_name)
        .order_by(func.count(ComplianceResult.id).desc())
        .limit(10)
        .all()
    )
    top_violated_rules = [
        {"rule_id": r.rule_id, "rule_name": r.rule_name, "violations": r.violations}
        for r in top_rules_rows
    ]

    return {
        "total_findings": total,
        "passed": passed,
        "failed": failed,
        "compliance_percentage": compliance_percentage,
        "severity_breakdown": severity_breakdown,
        "findings_by_framework": dict(framework_counter),
        "top_violated_rules": top_violated_rules,
    }
