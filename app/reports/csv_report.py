"""
CSV report generator. Exports the full compliance_results table (optionally
filtered) to a CSV file using pandas.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.database.models import ComplianceResult
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def generate_csv_report(db: Session, filename: str | None = None) -> Path:
    """
    Export all compliance results to a timestamped CSV file.

    Args:
        db: Active SQLAlchemy session.
        filename: Optional explicit filename; auto-generated if omitted.

    Returns:
        Path to the generated CSV file.
    """
    rows = db.query(ComplianceResult).order_by(ComplianceResult.id.asc()).all()

    data = [
        {
            "ID": r.id,
            "Resource Name": r.resource_name,
            "Resource Type": r.resource_type,
            "Rule ID": r.rule_id,
            "Rule Name": r.rule_name,
            "Severity": r.severity,
            "Status": r.status,
            "Framework": r.framework,
            "Recommendation": r.recommendation,
            "Scan Time": r.scan_time.isoformat(),
        }
        for r in rows
    ]

    df = pd.DataFrame(data)

    if filename is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.csv"

    output_path = settings.reports_dir / filename
    df.to_csv(output_path, index=False)
    logger.info("CSV report generated at %s (%d rows)", output_path, len(df))
    return output_path
