"""
Centralized application configuration.

All configuration values are loaded from environment variables (and a local
.env file, if present) so that no values are hardcoded anywhere else in the
codebase. This module is the single source of truth for paths, database
connection strings, and runtime settings.
"""

import os
from pathlib import Path
from functools import lru_cache

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional. If it is not installed we simply rely on
    # variables already present in the environment (e.g. injected by Docker).
    pass

# Absolute path to the project root (two levels up from this file:
# app/utils/config.py -> app/utils -> app -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings:
    """
    Application settings, populated from environment variables with sane
    local-development defaults. Instantiated once via get_settings().
    """

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "Security Compliance Dashboard")
        self.app_env: str = os.getenv("APP_ENV", "local")
        self.app_host: str = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port: int = int(os.getenv("APP_PORT", "8000"))

        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_file: Path = self._resolve(os.getenv("LOG_FILE", "logs/scanner.log"))

        self.database_url: str = os.getenv(
            "DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'database' / 'compliance.db'}"
        )

        self.resources_file: Path = self._resolve(
            os.getenv("RESOURCES_FILE", "app/resources/resources.json")
        )
        self.rules_dir: Path = self._resolve(os.getenv("RULES_DIR", "app/rules"))
        self.framework_mapping_file: Path = self._resolve(
            os.getenv("FRAMEWORK_MAPPING_FILE", "app/rules/framework_mapping.json")
        )

        self.reports_dir: Path = self._resolve(
            os.getenv("REPORTS_DIR", "reports_output")
        )

        # Ensure directories that must exist are created on startup.
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve(relative_path: str) -> Path:
        """Resolve a path relative to the project root into an absolute Path."""
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return (PROJECT_ROOT / path).resolve()


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()
