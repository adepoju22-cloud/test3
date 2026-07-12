"""
Unit tests for the scanner loader and engine.

Run with:  pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.schemas import Resource, Rule, FindingStatus
from app.scanner.engine import evaluate_rule, scan
from app.scanner.loader import load_resources, load_rules


def make_vm(encrypted: bool, public_ip: bool = False) -> Resource:
    """Helper to build a minimal VirtualMachine resource for tests."""
    return Resource(
        id="res-test-1",
        name="test-vm",
        type="VirtualMachine",
        properties={"encrypted": encrypted, "public_ip": public_ip, "mfa": True},
    )


def make_encryption_rule() -> Rule:
    """Helper to build a minimal encryption rule for tests."""
    return Rule(
        id="TEST-001",
        title="Test Disk Encryption",
        description="Disks must be encrypted",
        severity="Critical",
        resource_type="VirtualMachine",
        field="encrypted",
        operator="equals",
        expected_value=True,
        recommendation="Enable encryption",
        framework_mapping={"cis": "CIS-001", "nist": "SC-28", "iso27001": "A.8.24"},
    )


def test_evaluate_rule_pass():
    """A compliant resource should evaluate to True (PASS)."""
    resource = make_vm(encrypted=True)
    rule = make_encryption_rule()
    assert evaluate_rule(resource, rule) is True


def test_evaluate_rule_fail():
    """A non-compliant resource should evaluate to False (FAIL)."""
    resource = make_vm(encrypted=False)
    rule = make_encryption_rule()
    assert evaluate_rule(resource, rule) is False


def test_evaluate_rule_missing_field_fails_safely():
    """A resource missing the evaluated field should fail, not crash."""
    resource = Resource(
        id="res-test-2", name="no-props-vm", type="VirtualMachine", properties={}
    )
    rule = make_encryption_rule()
    assert evaluate_rule(resource, rule) is False


def test_scan_only_applies_matching_resource_type():
    """Rules should only be applied to resources of the matching type."""
    vm = make_vm(encrypted=True)
    storage_rule = Rule(
        id="TEST-002",
        title="Storage rule",
        description="desc",
        severity="High",
        resource_type="Storage",
        field="encrypted",
        expected_value=True,
        recommendation="rec",
        framework_mapping={"cis": "CIS-099"},
    )
    findings = scan([vm], [storage_rule])
    assert findings == []


def test_scan_generates_one_finding_per_applicable_rule():
    """Each (resource, applicable rule) pair should yield exactly one finding."""
    vm = make_vm(encrypted=True)
    rule = make_encryption_rule()
    findings = scan([vm], [rule])
    assert len(findings) == 1
    assert findings[0].status == FindingStatus.PASS_
    assert findings[0].rule_id == "TEST-001"
    assert "CIS:CIS-001" in findings[0].framework


def test_load_resources_returns_thirty_resources():
    """The bundled sample inventory should contain at least 30 resources."""
    resources = load_resources()
    assert len(resources) >= 30


def test_load_rules_returns_at_least_forty_rules():
    """The bundled rule set should contain at least 40 rules."""
    rules = load_rules()
    assert len(rules) >= 40


def test_full_scan_runs_without_error():
    """A full scan over the bundled sample data should run end-to-end."""
    resources = load_resources()
    rules = load_rules()
    findings = scan(resources, rules)
    assert len(findings) > 0
    statuses = {f.status for f in findings}
    assert statuses.issubset({FindingStatus.PASS_, FindingStatus.FAIL})
