"""
Core compliance scanning engine.

Workflow (per FEATURE 4 of the spec):
    1. Load resources
    2. Load rules
    3. Loop over every resource
    4. Evaluate every applicable rule (matching resource_type)
    5. Generate PASS or FAIL
    6. Generate a Finding
    7. Return all findings for persistence
"""

import operator as op
from datetime import datetime
from typing import Any, Callable

from app.models.schemas import Finding, FindingStatus, Resource, Rule
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Supported comparison operators a rule may declare. Defaults to "equals".
_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "equals": op.eq,
    "not_equals": op.ne,
    "greater_than": op.gt,
    "less_than": op.lt,
    "greater_than_or_equal": op.ge,
    "less_than_or_equal": op.le,
    "contains": lambda actual, expected: expected in actual
    if actual is not None
    else False,
    "exists": lambda actual, expected: (actual is not None) is bool(expected),
}


def _format_framework(rule: Rule) -> str:
    """Render a rule's framework mapping as a compact, queryable string."""
    mapping = rule.framework_mapping
    parts = []
    if mapping.cis:
        parts.append(f"CIS:{mapping.cis}")
    if mapping.nist:
        parts.append(f"NIST:{mapping.nist}")
    if mapping.iso27001:
        parts.append(f"ISO27001:{mapping.iso27001}")
    return "; ".join(parts) if parts else "Unmapped"


def evaluate_rule(resource: Resource, rule: Rule) -> bool:
    """
    Evaluate a single rule against a single resource's properties.

    Args:
        resource: The resource being evaluated.
        rule: The rule to apply.

    Returns:
        True if the resource satisfies the rule (PASS), False otherwise (FAIL).
    """
    actual_value = resource.properties.get(rule.field)
    comparator = _OPERATORS.get(rule.operator, op.eq)

    try:
        return bool(comparator(actual_value, rule.expected_value))
    except TypeError:
        # Mismatched types (e.g. comparing None with a bool) are treated as
        # a failed control rather than crashing the entire scan.
        logger.debug(
            "Type mismatch evaluating rule %s on resource %s (actual=%r, expected=%r)",
            rule.id,
            resource.name,
            actual_value,
            rule.expected_value,
        )
        return False


def scan(resources: list[Resource], rules: list[Rule]) -> list[Finding]:
    """
    Run every applicable rule against every resource.

    A rule is "applicable" to a resource when rule.resource_type matches
    resource.type. Findings are generated for every (resource, rule) pair
    that applies, recording either PASS or FAIL.

    Args:
        resources: The resource inventory to scan.
        rules: The compliance rules to evaluate.

    Returns:
        A list of Finding objects, one per applicable (resource, rule) pair.
    """
    findings: list[Finding] = []
    scan_time = datetime.utcnow()

    rules_by_type: dict[str, list[Rule]] = {}
    for rule in rules:
        rules_by_type.setdefault(rule.resource_type.value, []).append(rule)

    for resource in resources:
        applicable_rules = rules_by_type.get(resource.type.value, [])
        for rule in applicable_rules:
            passed = evaluate_rule(resource, rule)
            findings.append(
                Finding(
                    resource_id=resource.id,
                    resource_name=resource.name,
                    resource_type=resource.type,
                    rule_id=rule.id,
                    rule_name=rule.title,
                    severity=rule.severity,
                    status=FindingStatus.PASS_ if passed else FindingStatus.FAIL,
                    framework=_format_framework(rule),
                    recommendation=rule.recommendation,
                    scan_time=scan_time,
                )
            )

    passed_count = sum(1 for f in findings if f.status == FindingStatus.PASS_)
    failed_count = len(findings) - passed_count
    logger.info(
        "Scan complete: %d resources, %d rules, %d findings (%d PASS / %d FAIL)",
        len(resources),
        len(rules),
        len(findings),
        passed_count,
        failed_count,
    )
    return findings
