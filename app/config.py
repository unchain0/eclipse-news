import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    database_url: str
    scrape_interval_seconds: int
    allowed_origins: list[str]


def _parse_allowed_origins(value: str) -> list[str]:
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", "")
    scrape_interval_raw = os.getenv("SCRAPE_INTERVAL_SECONDS", "60")
    try:
        scrape_interval_seconds = int(scrape_interval_raw)
    except ValueError:
        scrape_interval_seconds = 60

    allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
    allowed_origins = _parse_allowed_origins(allowed_origins_raw)

    return Settings(
        database_url=database_url,
        scrape_interval_seconds=scrape_interval_seconds,
        allowed_origins=allowed_origins,
    )


settings = get_settings()
