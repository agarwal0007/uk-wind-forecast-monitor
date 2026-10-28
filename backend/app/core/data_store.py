"""Loads the cached Elexon data into memory (once per process)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.config import Settings, get_settings

log = logging.getLogger(__name__)

ACTUALS_FILE = "actuals.json"
FORECASTS_FILE = "forecasts.json"


@dataclass(frozen=True)
class DataStore:
    actuals: pd.DataFrame  # startTime, actual
    forecasts: pd.DataFrame  # startTime, publishTime, forecast


def write_json(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame as compact columnar JSON with ISO-8601 UTC timestamps."""
    out: dict[str, list[object]] = {}
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            out[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist()
        else:
            out[col] = df[col].tolist()
    path.write_text(json.dumps(out, separators=(",", ":")))


def read_json(path: Path, time_cols: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(json.loads(path.read_text()))
    for col in time_cols:
        df[col] = pd.to_datetime(df[col], utc=True)
    return df


def _load(settings: Settings) -> DataStore:
    actuals_path = settings.data_dir / ACTUALS_FILE
    forecasts_path = settings.data_dir / FORECASTS_FILE
    if actuals_path.exists() and forecasts_path.exists():
        actuals = read_json(actuals_path, ["startTime"])
        forecasts = read_json(forecasts_path, ["startTime", "publishTime"])
    elif settings.live_fetch:
        from app.ingest.elexon import ElexonClient

        log.warning("Cache missing in %s; fetching live from Elexon", settings.data_dir)
        client = ElexonClient(settings.elexon_base_url)
        actuals = client.fetch_actuals(
            settings.target_start.date(), settings.target_end.date()
        )
        forecasts = client.fetch_forecasts(
            settings.publish_start.date(), settings.target_end.date()
        )
    else:
        raise FileNotFoundError(
            f"No cached data in {settings.data_dir}. Run scripts/fetch_data.py "
            "or set LIVE_FETCH=true."
        )
    actuals["actual"] = actuals["actual"].astype(float)
    forecasts["forecast"] = forecasts["forecast"].astype(float)
    return DataStore(actuals=actuals, forecasts=forecasts)


@lru_cache
def get_store() -> DataStore:
    return _load(get_settings())
