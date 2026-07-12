"""
SQLAlchemy ORM models for the Security Compliance Dashboard.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Index

from app.database.db import Base


class ComplianceResult(Base):
    """
    Stores the outcome of evaluating a single rule against a single
    resource during a scan. This is the central table that powers the
    REST API, the CSV/PDF reports, and the Grafana dashboards.
    """

    __tablename__ = "compliance_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_name = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    rule_id = Column(String(50), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(10), nullable=False, index=True)  # PASS / FAIL
    framework = Column(String(255), nullable=False)
    recommendation = Column(String(1000), nullable=False)
    scan_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_results_status_severity", "status", "severity"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr is cosmetic
        return (
            f"<ComplianceResult id={self.id} resource={self.resource_name} "
            f"rule={self.rule_id} status={self.status}>"
        )
