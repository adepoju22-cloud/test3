"""
Pydantic schemas used across the API, scanner, and services layers.

These models provide runtime input validation and typed serialization for
resources, rules, findings, and API responses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class Severity(str, Enum):
    """Allowed severity levels for a compliance rule / finding."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class FindingStatus(str, Enum):
    """Outcome of evaluating a single rule against a single resource."""

    PASS_ = "PASS"
    FAIL = "FAIL"


class ResourceType(str, Enum):
    """Supported resource types in the local inventory."""

    VIRTUAL_MACHINE = "VirtualMachine"
    STORAGE = "Storage"
    DATABASE = "Database"
    NETWORK = "Network"
    FIREWALL = "Firewall"
    USER = "User"


class Resource(BaseModel):
    """A single inventoried resource loaded from resources/resources.json."""

    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    type: ResourceType
    properties: dict[str, Any] = Field(default_factory=dict)


class FrameworkMapping(BaseModel):
    """Maps a single rule to its equivalent control IDs in each framework."""

    cis: Optional[str] = None
    nist: Optional[str] = None
    iso27001: Optional[str] = None


class Rule(BaseModel):
    """A single compliance rule loaded from a YAML rule file."""

    id: str
    title: str
    description: str
    severity: Severity
    resource_type: ResourceType
    field: str
    operator: str = "equals"
    expected_value: Any
    recommendation: str
    framework_mapping: FrameworkMapping


class Finding(BaseModel):
    """The result of evaluating one rule against one resource."""

    resource_id: str
    resource_name: str
    resource_type: ResourceType
    rule_id: str
    rule_name: str
    severity: Severity
    status: FindingStatus
    framework: str
    recommendation: str
    scan_time: datetime = Field(default_factory=datetime.utcnow)


class ComplianceResultOut(BaseModel):
    """API response shape for a single stored compliance result row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_name: str
    resource_type: str
    rule_id: str
    rule_name: str
    severity: str
    status: str
    framework: str
    recommendation: str
    scan_time: datetime


class SeverityBreakdown(BaseModel):
    """Counts of findings grouped by severity."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class SummaryResponse(BaseModel):
    """API response shape for GET /summary."""

    total_findings: int
    passed: int
    failed: int
    compliance_percentage: float
    severity_breakdown: SeverityBreakdown
    findings_by_framework: dict[str, int]
    top_violated_rules: list[dict[str, Any]]


class ScanResponse(BaseModel):
    """API response shape for POST /scan."""

    message: str
    resources_scanned: int
    rules_evaluated: int
    findings_generated: int
    passed: int
    failed: int
    scan_time: datetime
