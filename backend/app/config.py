"""Application configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


def load_env_files() -> None:
    """Load `.env` from repository root and current working directory (if present)."""
    from dotenv import load_dotenv

    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")
    load_dotenv()


def parse_cors_allowed_origins(raw: str | None) -> tuple[str, ...]:
    """
    CORS allowlist for browser clients.

    `*` (default) allows any origin — convenient for local dev.
    Production split-hosting: set comma-separated origins, e.g.
    `https://windlens.example.com,http://localhost:5173`.
    """
    value = (raw or "*").strip()
    if value == "*":
        return ("*",)
    parts = tuple(origin.strip() for origin in value.split(",") if origin.strip())
    return parts or ("*",)


@dataclass(frozen=True)
class Settings:
    elexon_base_url: str
    delivery_start: date
    delivery_end: date
    decision_cutoff_local_time: str  # HH:MM
    decision_cutoff_timezone: str
    windfor_publish_from: str  # ISO UTC for historical fetch window
    windfor_publish_to: str
    elexon_source_cache_ttl_seconds: float
    cors_allowed_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> Settings:
        load_env_files()
        return cls(
            elexon_base_url=os.getenv(
                "ELEXON_BASE_URL",
                "https://data.elexon.co.uk/bmrs/api/v1",
            ).rstrip("/"),
            delivery_start=date.fromisoformat(
                os.getenv("DELIVERY_START_DATE", "2026-01-01"),
            ),
            delivery_end=date.fromisoformat(
                os.getenv("DELIVERY_END_DATE", "2026-01-31"),
            ),
            decision_cutoff_local_time=os.getenv("DECISION_CUTOFF_LOCAL_TIME", "09:20"),
            decision_cutoff_timezone=os.getenv("DECISION_CUTOFF_TIMEZONE", "Europe/London"),
            windfor_publish_from=os.getenv(
                "WINDFOR_PUBLISH_FROM",
                "2025-12-25T00:00:00Z",
            ),
            windfor_publish_to=os.getenv(
                "WINDFOR_PUBLISH_TO",
                "2026-01-31T23:59:59Z",
            ),
            elexon_source_cache_ttl_seconds=float(
                os.getenv("ELEXON_SOURCE_CACHE_TTL_SECONDS", "3600"),
            ),
            cors_allowed_origins=parse_cors_allowed_origins(
                os.getenv("CORS_ALLOWED_ORIGINS"),
            ),
        )


def get_settings() -> Settings:
    return Settings.from_env()
