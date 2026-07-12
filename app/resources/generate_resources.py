"""
One-off generator script for sample test data (FEATURE 11 / BONUS).

Produces:
    app/resources/resources.json   -> 30 fake resources across 6 types
    app/rules/cis.yaml             -> 40 compliance rules
    app/rules/framework_mapping.json -> CIS/NIST/ISO27001 reference table

Run with:
    python -m app.resources.generate_resources
"""

import json
import random
from pathlib import Path

import yaml

RESOURCES_DIR = Path(__file__).resolve().parent
RULES_DIR = RESOURCES_DIR.parent / "rules"

random.seed(42)

RESOURCE_TYPES = [
    "VirtualMachine",
    "Storage",
    "Database",
    "Network",
    "Firewall",
    "User",
]

# Property templates per resource type. Each entry is (field_name, choices).
PROPERTY_TEMPLATES: dict[str, list[tuple[str, list]]] = {
    "VirtualMachine": [
        ("encrypted", [True, False]),
        ("public_ip", [True, False]),
        ("mfa", [True, False]),
        ("os_patched", [True, False]),
        ("backup_enabled", [True, False]),
        ("monitoring_agent_installed", [True, False]),
        ("endpoint_protection_enabled", [True, False]),
        ("disk_snapshot_enabled", [True, False]),
    ],
    "Storage": [
        ("encrypted", [True, False]),
        ("public_access", [True, False]),
        ("versioning_enabled", [True, False]),
        ("access_logging_enabled", [True, False]),
        ("lifecycle_policy_enabled", [True, False]),
        ("encryption_in_transit_enforced", [True, False]),
        ("soft_delete_enabled", [True, False]),
    ],
    "Database": [
        ("encrypted", [True, False]),
        ("public_access", [True, False]),
        ("backup_enabled", [True, False]),
        ("ssl_enforced", [True, False]),
        ("audit_logging_enabled", [True, False]),
        ("automatic_patching", [True, False]),
        ("least_privilege_db_roles", [True, False]),
        ("network_isolation_enabled", [True, False]),
    ],
    "Network": [
        ("flow_logs_enabled", [True, False]),
        ("default_deny", [True, False]),
        ("segmentation_enabled", [True, False]),
        ("dns_logging_enabled", [True, False]),
        ("nat_gateway_used", [True, False]),
        ("private_endpoints_enabled", [True, False]),
    ],
    "Firewall": [
        ("default_deny_inbound", [True, False]),
        ("logging_enabled", [True, False]),
        ("unrestricted_ports_open", [True, False]),
        ("rules_reviewed_last_90_days", [True, False]),
        ("geo_blocking_enabled", [True, False]),
        ("intrusion_detection_enabled", [True, False]),
    ],
    "User": [
        ("mfa_enabled", [True, False]),
        ("password_expiry_enabled", [True, False]),
        ("admin_privileges", [True, False]),
        ("inactive_over_90_days", [True, False]),
        ("least_privilege_applied", [True, False]),
        ("service_account_reviewed", [True, False]),
        ("privileged_access_workstation_used", [True, False]),
    ],
}

NAME_PREFIXES = {
    "VirtualMachine": "vm",
    "Storage": "storage",
    "Database": "db",
    "Network": "vnet",
    "Firewall": "fw",
    "User": "user",
}


def generate_resources(count_per_type: int = 5) -> dict:
    """Generate a balanced set of fake resources across all resource types."""
    resources = []
    counter = 1
    for r_type in RESOURCE_TYPES:
        for i in range(count_per_type):
            properties = {
                field: random.choice(choices)
                for field, choices in PROPERTY_TEMPLATES[r_type]
            }
            resources.append(
                {
                    "id": f"res-{counter:04d}",
                    "name": f"{NAME_PREFIXES[r_type]}{i + 1:02d}",
                    "type": r_type,
                    "properties": properties,
                }
            )
            counter += 1
    return {"resources": resources}


# (field, severity, title, description, recommendation, cis, nist, iso)
RULE_DEFINITIONS: dict[str, list[tuple]] = {
    "VirtualMachine": [
        (
            "encrypted",
            True,
            "Critical",
            "VM Disk Encryption",
            "Ensure virtual machine disks are encrypted at rest.",
            "Enable disk encryption for all virtual machine volumes.",
            "CIS-001",
            "SC-28",
            "A.8.24",
        ),
        (
            "public_ip",
            False,
            "High",
            "VM No Public IP",
            "Virtual machines should not be directly exposed to the internet.",
            "Remove public IP addresses and route traffic through a load balancer or bastion host.",
            "CIS-002",
            "SC-7",
            "A.8.20",
        ),
        (
            "mfa",
            True,
            "Critical",
            "VM Login MFA Required",
            "Multi-factor authentication should be required for VM login.",
            "Enforce MFA for all administrative access to virtual machines.",
            "CIS-003",
            "IA-2",
            "A.5.17",
        ),
        (
            "os_patched",
            True,
            "High",
            "VM OS Patch Compliance",
            "Operating system should be patched to the latest security baseline.",
            "Apply outstanding OS security patches and enable automatic patching.",
            "CIS-004",
            "SI-2",
            "A.8.8",
        ),
        (
            "backup_enabled",
            True,
            "Medium",
            "VM Backup Enabled",
            "Virtual machines should have automated backups enabled.",
            "Enable scheduled backups with a retention policy of at least 30 days.",
            "CIS-005",
            "CP-9",
            "A.8.13",
        ),
        (
            "monitoring_agent_installed",
            True,
            "Low",
            "VM Monitoring Agent Installed",
            "A monitoring/telemetry agent should be installed for observability.",
            "Install and enable the monitoring agent on all virtual machines.",
            "CIS-006",
            "SI-4",
            "A.8.16",
        ),
        (
            "endpoint_protection_enabled",
            True,
            "High",
            "VM Endpoint Protection Enabled",
            "Endpoint protection (anti-malware/EDR) should be enabled on all VMs.",
            "Deploy and enable an endpoint protection / EDR agent on all virtual machines.",
            "CIS-007",
            "SI-3",
            "A.8.7",
        ),
        (
            "disk_snapshot_enabled",
            True,
            "Low",
            "VM Disk Snapshot Enabled",
            "Periodic disk snapshots should be enabled to support recovery.",
            "Schedule periodic disk snapshots in addition to standard backups.",
            "CIS-008",
            "CP-9",
            "A.8.13",
        ),
    ],
    "Storage": [
        (
            "encrypted",
            True,
            "Critical",
            "Storage Encryption At Rest",
            "Storage accounts/buckets should be encrypted at rest.",
            "Enable server-side encryption using a managed or customer-managed key.",
            "CIS-010",
            "SC-28",
            "A.8.24",
        ),
        (
            "public_access",
            False,
            "Critical",
            "Storage No Public Access",
            "Storage containers should not allow anonymous public access.",
            "Disable public access and use signed URLs or IAM policies instead.",
            "CIS-011",
            "AC-3",
            "A.8.3",
        ),
        (
            "versioning_enabled",
            True,
            "Medium",
            "Storage Versioning Enabled",
            "Object versioning should be enabled to protect against accidental deletion.",
            "Enable versioning on all storage containers holding production data.",
            "CIS-012",
            "CP-9",
            "A.8.13",
        ),
        (
            "access_logging_enabled",
            True,
            "High",
            "Storage Access Logging Enabled",
            "Access logging should be enabled for audit and forensic purposes.",
            "Enable access logging and route logs to a centralized log store.",
            "CIS-013",
            "AU-2",
            "A.8.15",
        ),
        (
            "lifecycle_policy_enabled",
            True,
            "Low",
            "Storage Lifecycle Policy Enabled",
            "A lifecycle policy should be defined to manage data retention costs.",
            "Define a lifecycle policy to transition or expire old objects.",
            "CIS-014",
            "SI-12",
            "A.5.33",
        ),
        (
            "encryption_in_transit_enforced",
            True,
            "High",
            "Storage Encryption In Transit Enforced",
            "Storage endpoints should reject unencrypted (non-HTTPS) connections.",
            "Enforce HTTPS-only access on all storage endpoints.",
            "CIS-015",
            "SC-8",
            "A.8.24",
        ),
        (
            "soft_delete_enabled",
            True,
            "Medium",
            "Storage Soft Delete Enabled",
            "Soft delete should be enabled to protect against accidental or malicious deletion.",
            "Enable soft delete with a recovery window of at least 14 days.",
            "CIS-016",
            "CP-9",
            "A.8.13",
        ),
    ],
    "Database": [
        (
            "encrypted",
            True,
            "Critical",
            "Database Encryption At Rest",
            "Databases should be encrypted at rest.",
            "Enable transparent data encryption (TDE) on all database instances.",
            "CIS-020",
            "SC-28",
            "A.8.24",
        ),
        (
            "public_access",
            False,
            "Critical",
            "Database No Public Access",
            "Databases should not be publicly accessible from the internet.",
            "Restrict database access to private network ranges and VPN/bastion only.",
            "CIS-021",
            "SC-7",
            "A.8.20",
        ),
        (
            "ssl_enforced",
            True,
            "High",
            "Database SSL/TLS Enforced",
            "Connections to the database should require SSL/TLS encryption in transit.",
            "Enforce SSL/TLS for all client connections to the database.",
            "CIS-022",
            "SC-8",
            "A.8.24",
        ),
        (
            "backup_enabled",
            True,
            "Medium",
            "Database Automated Backups",
            "Automated backups should be enabled with point-in-time recovery.",
            "Enable automated backups with at least a 7-day retention window.",
            "CIS-023",
            "CP-9",
            "A.8.13",
        ),
        (
            "audit_logging_enabled",
            True,
            "High",
            "Database Audit Logging Enabled",
            "Database audit logging should capture all administrative and DML actions.",
            "Enable audit logging and forward logs to a centralized SIEM.",
            "CIS-024",
            "AU-2",
            "A.8.15",
        ),
        (
            "automatic_patching",
            True,
            "Medium",
            "Database Automatic Patching",
            "Database engine should receive security patches automatically.",
            "Enable the automatic minor-version patching maintenance window.",
            "CIS-025",
            "SI-2",
            "A.8.8",
        ),
        (
            "least_privilege_db_roles",
            True,
            "Medium",
            "Database Least Privilege Roles",
            "Database roles should be scoped to least privilege rather than broad admin grants.",
            "Review database role assignments and remove unnecessary privileged grants.",
            "CIS-026",
            "AC-6",
            "A.5.18",
        ),
        (
            "network_isolation_enabled",
            True,
            "High",
            "Database Network Isolation",
            "Databases should be deployed inside an isolated private subnet.",
            "Place the database in a private subnet with no direct internet route.",
            "CIS-027",
            "SC-7",
            "A.8.22",
        ),
    ],
    "Network": [
        (
            "flow_logs_enabled",
            True,
            "High",
            "Network Flow Logs Enabled",
            "VPC/VNet flow logs should be enabled for traffic visibility.",
            "Enable flow logging and route logs to a central analysis workspace.",
            "CIS-030",
            "AU-2",
            "A.8.15",
        ),
        (
            "default_deny",
            True,
            "Critical",
            "Network Default Deny Posture",
            "Network security groups should default to deny-all inbound traffic.",
            "Set the default inbound rule to deny and explicitly allow required ports only.",
            "CIS-031",
            "AC-4",
            "A.8.20",
        ),
        (
            "segmentation_enabled",
            True,
            "Medium",
            "Network Segmentation Enabled",
            "Production and non-production workloads should be network-segmented.",
            "Apply subnet-level segmentation and restrict inter-subnet routing.",
            "CIS-032",
            "SC-7",
            "A.8.22",
        ),
        (
            "dns_logging_enabled",
            True,
            "Low",
            "Network DNS Query Logging",
            "DNS query logging should be enabled to detect anomalous resolution patterns.",
            "Enable DNS query logging and forward to the SIEM for analysis.",
            "CIS-033",
            "AU-2",
            "A.8.16",
        ),
        (
            "nat_gateway_used",
            True,
            "Medium",
            "Network NAT Gateway For Outbound Traffic",
            "Outbound internet traffic from private subnets should route through a managed NAT gateway.",
            "Deploy a managed NAT gateway instead of assigning public IPs to private resources.",
            "CIS-034",
            "SC-7",
            "A.8.20",
        ),
        (
            "private_endpoints_enabled",
            True,
            "High",
            "Network Private Endpoints Enabled",
            "Sensitive services should be reachable via private endpoints, not the public internet.",
            "Enable private endpoints/private link for PaaS services used on this network.",
            "CIS-035",
            "SC-7",
            "A.8.22",
        ),
    ],
    "Firewall": [
        (
            "default_deny_inbound",
            True,
            "Critical",
            "Firewall Default Deny Inbound",
            "Firewalls should default to denying inbound traffic unless explicitly allowed.",
            "Configure the firewall's default inbound policy to DENY.",
            "CIS-040",
            "AC-4",
            "A.8.20",
        ),
        (
            "logging_enabled",
            True,
            "High",
            "Firewall Logging Enabled",
            "Firewall rule hits should be logged for audit and incident response.",
            "Enable logging on all firewall rules and forward to centralized storage.",
            "CIS-041",
            "AU-2",
            "A.8.15",
        ),
        (
            "unrestricted_ports_open",
            False,
            "Critical",
            "Firewall No Unrestricted Ports",
            "Firewalls should not expose administrative ports (22, 3389, etc.) to 0.0.0.0/0.",
            "Restrict administrative ports to known IP ranges or a bastion host.",
            "CIS-042",
            "SC-7",
            "A.8.20",
        ),
        (
            "rules_reviewed_last_90_days",
            True,
            "Medium",
            "Firewall Rules Reviewed Periodically",
            "Firewall rule sets should be reviewed at least every 90 days.",
            "Establish a quarterly review process for firewall rule sets.",
            "CIS-043",
            "CA-7",
            "A.5.36",
        ),
        (
            "geo_blocking_enabled",
            True,
            "Low",
            "Firewall Geo-Blocking Enabled",
            "Geo-blocking should restrict traffic from regions with no business need.",
            "Enable geo-blocking rules for regions outside the organization's operating footprint.",
            "CIS-044",
            "SC-7",
            "A.8.20",
        ),
        (
            "intrusion_detection_enabled",
            True,
            "High",
            "Firewall Intrusion Detection Enabled",
            "An intrusion detection/prevention capability should be enabled on perimeter firewalls.",
            "Enable IDS/IPS signatures on all perimeter firewall devices.",
            "CIS-045",
            "SI-4",
            "A.8.16",
        ),
    ],
    "User": [
        (
            "mfa_enabled",
            True,
            "Critical",
            "User MFA Enabled",
            "All user accounts should have multi-factor authentication enabled.",
            "Enforce MFA enrollment for all user accounts, especially privileged ones.",
            "CIS-050",
            "IA-2",
            "A.5.17",
        ),
        (
            "password_expiry_enabled",
            True,
            "Medium",
            "User Password Expiry Policy",
            "User accounts should be subject to a password expiry policy.",
            "Enable password expiration and complexity requirements.",
            "CIS-051",
            "IA-5",
            "A.5.17",
        ),
        (
            "admin_privileges",
            False,
            "High",
            "User Least Privilege (No Standing Admin)",
            "Standard user accounts should not retain standing administrative privileges.",
            "Move administrative access to just-in-time elevation with approval workflows.",
            "CIS-052",
            "AC-6",
            "A.5.18",
        ),
        (
            "inactive_over_90_days",
            False,
            "Medium",
            "User No Stale Inactive Accounts",
            "Accounts inactive for more than 90 days should be disabled or removed.",
            "Disable or remove accounts with no sign-in activity for 90+ days.",
            "CIS-053",
            "AC-2",
            "A.5.18",
        ),
        (
            "least_privilege_applied",
            True,
            "Low",
            "User Least Privilege Role Assignment",
            "User role assignments should follow the principle of least privilege.",
            "Review and right-size role assignments based on job function.",
            "CIS-054",
            "AC-6",
            "A.5.15",
        ),
        (
            "service_account_reviewed",
            True,
            "Medium",
            "Service Account Periodically Reviewed",
            "Service/non-human accounts should be reviewed periodically for continued need.",
            "Review service accounts quarterly and disable unused credentials.",
            "CIS-055",
            "AC-2",
            "A.5.18",
        ),
        (
            "privileged_access_workstation_used",
            True,
            "High",
            "Privileged Access Workstation Required",
            "Privileged administrative actions should be performed from a hardened, dedicated workstation.",
            "Require privileged access workstations (PAWs) for all administrative activity.",
            "CIS-056",
            "AC-6",
            "A.8.1",
        ),
    ],
}


def generate_rules() -> dict:
    """Build the full list of compliance rules from RULE_DEFINITIONS."""
    rules = []
    for resource_type, definitions in RULE_DEFINITIONS.items():
        for (
            field,
            expected,
            severity,
            title,
            description,
            recommendation,
            cis,
            nist,
            iso,
        ) in definitions:
            rules.append(
                {
                    "id": cis,
                    "title": title,
                    "description": description,
                    "severity": severity,
                    "resource_type": resource_type,
                    "field": field,
                    "operator": "equals",
                    "expected_value": expected,
                    "recommendation": recommendation,
                    "framework_mapping": {
                        "cis": cis,
                        "nist": nist,
                        "iso27001": iso,
                    },
                }
            )
    return {"rules": rules}


def generate_framework_mapping(rules: dict) -> dict:
    """Build a standalone CIS -> NIST -> ISO27001 reference table."""
    mapping = {}
    for rule in rules["rules"]:
        mapping[rule["id"]] = {
            "title": rule["title"],
            "cis": rule["framework_mapping"]["cis"],
            "nist": rule["framework_mapping"]["nist"],
            "iso27001": rule["framework_mapping"]["iso27001"],
        }
    return mapping


def main() -> None:
    """Generate and write resources.json, cis.yaml, and framework_mapping.json."""
    resources = generate_resources(count_per_type=5)
    rules = generate_rules()
    framework_mapping = generate_framework_mapping(rules)

    resources_path = RESOURCES_DIR / "resources.json"
    resources_path.write_text(json.dumps(resources, indent=2), encoding="utf-8")

    RULES_DIR.mkdir(parents=True, exist_ok=True)
    rules_path = RULES_DIR / "cis.yaml"
    with rules_path.open("w", encoding="utf-8") as fh:
        yaml.dump(rules, fh, sort_keys=False, default_flow_style=False)

    mapping_path = RULES_DIR / "framework_mapping.json"
    mapping_path.write_text(
        json.dumps(framework_mapping, indent=2), encoding="utf-8"
    )

    print(f"Generated {len(resources['resources'])} resources -> {resources_path}")
    print(f"Generated {len(rules['rules'])} rules -> {rules_path}")
    print(f"Generated framework mapping -> {mapping_path}")


if __name__ == "__main__":
    main()
