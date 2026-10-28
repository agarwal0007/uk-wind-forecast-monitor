"""Runtime configuration, read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", BACKEND_DIR / "data"))
    )
    elexon_base_url: str = field(
        default_factory=lambda: os.getenv(
            "ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1"
        )
    )
    # Fetch from Elexon at startup if the cached files are missing.
    live_fetch: bool = field(default_factory=lambda: _bool_env("LIVE_FETCH"))
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]
    )
    # Delivery (target) window the app covers: purchase decisions in Jan 2026.
    target_start: pd.Timestamp = pd.Timestamp("2026-01-02T00:00:00Z")
    target_end: pd.Timestamp = pd.Timestamp("2026-02-01T23:30:00Z")
    # Forecasts published from here onward are fetched (48h before target_start).
    publish_start: pd.Timestamp = pd.Timestamp("2025-12-30T00:00:00Z")


@lru_cache
def get_settings() -> Settings:
    return Settings()
