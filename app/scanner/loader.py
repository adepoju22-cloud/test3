"""
Loaders for resources (JSON) and compliance rules (YAML).

The rule loader automatically discovers every *.yaml / *.yml file inside
the configured rules directory, so new rule files can be dropped in
without touching any Python code (see Bonus requirement: auto-detection
of new rule files).
"""

import json
from pathlib import Path
from typing import Any

import yaml

from app.models.schemas import Resource, Rule
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ResourceLoadError(Exception):
    """Raised when the resource inventory file cannot be read or parsed."""


class RuleLoadError(Exception):
    """Raised when a rule file cannot be read or parsed."""


def load_resources(path: Path | None = None) -> list[Resource]:
    """
    Load and validate the resource inventory from JSON.

    Args:
        path: Optional override path. Defaults to settings.resources_file.

    Returns:
        A list of validated Resource objects.

    Raises:
        ResourceLoadError: If the file is missing or contains invalid data.
    """
    file_path = path or settings.resources_file
    if not file_path.exists():
        raise ResourceLoadError(f"Resources file not found: {file_path}")

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ResourceLoadError(f"Invalid JSON in {file_path}: {exc}") from exc

    resources: list[Resource] = []
    for index, item in enumerate(raw.get("resources", [])):
        try:
            resources.append(Resource(**item))
        except Exception as exc:  # pydantic ValidationError or similar
            logger.warning("Skipping invalid resource at index %d: %s", index, exc)

    logger.info("Loaded %d resources from %s", len(resources), file_path)
    return resources


def load_framework_mapping(path: Path | None = None) -> dict[str, Any]:
    """Load the framework mapping reference file (CIS / NIST / ISO27001)."""
    file_path = path or settings.framework_mapping_file
    if not file_path.exists():
        logger.warning("Framework mapping file not found: %s", file_path)
        return {}
    return json.loads(file_path.read_text(encoding="utf-8"))


def load_rules(rules_dir: Path | None = None) -> list[Rule]:
    """
    Discover and load every YAML rule file inside the rules directory.

    Args:
        rules_dir: Optional override directory. Defaults to settings.rules_dir.

    Returns:
        A list of validated Rule objects, aggregated across all YAML files.

    Raises:
        RuleLoadError: If the rules directory does not exist.
    """
    directory = rules_dir or settings.rules_dir
    if not directory.exists():
        raise RuleLoadError(f"Rules directory not found: {directory}")

    rule_files = sorted(
        [*directory.glob("*.yaml"), *directory.glob("*.yml")]
    )
    if not rule_files:
        logger.warning("No YAML rule files found in %s", directory)

    rules: list[Rule] = []
    for rule_file in rule_files:
        try:
            content = yaml.safe_load(rule_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            logger.error("Failed to parse %s: %s", rule_file, exc)
            continue

        for index, item in enumerate(content.get("rules", [])):
            try:
                rules.append(Rule(**item))
            except Exception as exc:
                logger.warning(
                    "Skipping invalid rule #%d in %s: %s", index, rule_file.name, exc
                )

        logger.info("Loaded rules from %s", rule_file.name)

    logger.info("Loaded %d total rules from %d file(s)", len(rules), len(rule_files))
    return rules
