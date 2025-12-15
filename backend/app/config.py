import os
import re
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    database_url: str = Field(..., min_length=1)
    scrape_interval_seconds: int = Field(..., ge=1)
    allowed_origins: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    max_retries: int = Field(default=3, ge=0)
    retry_delay_seconds: float = Field(default=1.0, ge=0.1)
    request_timeout_seconds: int = Field(default=10, ge=1)
    max_search_results: int = Field(default=1000, ge=1, le=10000)
    search_query_timeout_seconds: int = Field(default=5, ge=1)
    max_search_pattern_length: int = Field(default=50, ge=1, le=200)


def _parse_allowed_origins(value: str) -> list[str]:
    """Parse and validate comma-separated origins list."""
    if not value:
        return []

    origins: list[str] = []
    for origin in value.split(","):
        origin = origin.strip()
        if not origin:
            continue

        if not _is_valid_cors_origin(origin):
            continue

        origins.append(origin)

    return origins


def _parse_allowed_domains(value: str) -> list[str]:
    """Parse and validate comma-separated domains list."""
    if not value:
        return []

    domains: list[str] = []
    for domain in value.split(","):
        domain = domain.strip()
        if not domain:
            continue

        if not _is_valid_domain(domain):
            continue

        domains.append(domain)

    return domains


def _is_valid_cors_origin(origin: str) -> bool:
    """Validate CORS origin format to prevent broad CORS policies."""
    try:
        if not (origin.startswith("http://") or origin.startswith("https://")):
            return False

        parsed = urlparse(origin)

        if not parsed.hostname:
            return False

        if parsed.hostname in ("localhost", "0.0.0.0"):
            pass
        elif parsed.hostname.startswith("*"):
            return False

        if parsed.hostname.startswith(
            (
                "192.168.",
                "10.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
            )
        ):
            return False

        return True

    except Exception:
        return False


def _is_valid_domain(domain: str) -> bool:
    """Validate domain format."""
    try:
        if len(domain) > 253:
            return False

        if not re.match(r"^[a-zA-Z0-9.-]+$", domain):
            return False

        if (
            domain.startswith("-")
            or domain.endswith("-")
            or domain.startswith(".")
            or domain.endswith(".")
        ):
            return False

        if domain in ("localhost", "127.0.0.1"):
            return False

        return True

    except Exception:
        return False


def _validate_database_url(url: str) -> str:
    """Validate and sanitize DATABASE_URL to prevent dangerous connections."""
    try:
        if not url:
            raise ValueError("DATABASE_URL cannot be empty")

        parsed = urlparse(url)

        if parsed.scheme not in ("postgresql", "postgres"):
            raise ValueError(
                f"Invalid database scheme: {parsed.scheme}. Only 'postgresql' is allowed."
            )

        if not parsed.hostname:
            raise ValueError("DATABASE_URL must have a hostname")

        if parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
            pass
        elif parsed.hostname.startswith(
            (
                "192.168.",
                "10.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
            )
        ):
            raise ValueError("Private IP ranges not allowed in DATABASE_URL")

        if url.startswith(("file://", "sqlite:", "sqlite3:")):
            raise ValueError("File-based databases not allowed")

        return url

    except Exception as exc:
        raise ValueError(f"Invalid DATABASE_URL: {exc}")


def _get_env_int(key: str, default: int) -> int:
    """Get integer from environment variable with fallback."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    """Get float from environment variable with fallback."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def _parse_database_settings() -> dict[str, str | int]:
    """Parse and validate database and scraping settings."""
    database_url = os.getenv("DATABASE_URL", "")

    try:
        validated_url = _validate_database_url(database_url)
    except ValueError as exc:
        raise ValueError(f"DATABASE_URL validation failed: {exc}")

    return {
        "database_url": validated_url,
        "scrape_interval_seconds": _get_env_int("SCRAPE_INTERVAL_SECONDS", 60),
    }


def _parse_security_settings() -> dict[str, list[str] | int]:
    """Parse security and CORS settings."""
    return {
        "allowed_origins": _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS", "")),
        "allowed_domains": _parse_allowed_domains(os.getenv("ALLOWED_DOMAINS", "")),
    }


def _parse_request_settings() -> dict[str, int | float]:
    """Parse HTTP request and retry settings."""
    return {
        "max_retries": _get_env_int("MAX_RETRIES", 3),
        "retry_delay_seconds": _get_env_float("RETRY_DELAY_SECONDS", 1.0),
        "request_timeout_seconds": _get_env_int("REQUEST_TIMEOUT_SECONDS", 10),
    }


def _parse_search_settings() -> dict[str, int]:
    """Parse search and query settings."""
    return {
        "max_search_results": _get_env_int("MAX_SEARCH_RESULTS", 1000),
        "search_query_timeout_seconds": _get_env_int("SEARCH_QUERY_TIMEOUT_SECONDS", 5),
        "max_search_pattern_length": _get_env_int("MAX_SEARCH_PATTERN_LENGTH", 50),
    }


def get_settings() -> Settings:
    """Load and validate application settings from environment variables."""
    database_settings = _parse_database_settings()
    security_settings = _parse_security_settings()
    request_settings = _parse_request_settings()
    search_settings = _parse_search_settings()

    all_settings: dict[str, Any] = {
        **database_settings,
        **security_settings,
        **request_settings,
        **search_settings,
    }

    return Settings(**all_settings)


settings = get_settings()
