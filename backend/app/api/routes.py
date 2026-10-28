"""HTTP routes. Thin layer: parse/validate params, call core, shape responses."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, time
from functools import lru_cache
from typing import Annotated, Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas import (
    Health,
    HorizonRow,
    HourRow,
    Metrics,
    Selection,
    SeriesPoint,
)
from app.config import get_settings
from app.core import metrics
from app.core.data_store import get_store
from app.core.selection import MAX_HORIZON_H, build_series

router = APIRouter(prefix="/api")

CUTOFF_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


@dataclass(frozen=True)
class Params:
    start: pd.Timestamp
    end: pd.Timestamp
    mode: Literal["horizon", "decision"]
    horizon: int
    cutoff: time

    @property
    def selection(self) -> Selection:
        decision = self.mode == "decision"
        return Selection(
            start=self.start.to_pydatetime(),
            end=self.end.to_pydatetime(),
            mode=self.mode,
            horizon=None if decision else self.horizon,
            cutoff=self.cutoff.strftime("%H:%M") if decision else None,
        )


def _utc(dt: datetime | None, default: pd.Timestamp) -> pd.Timestamp:
    if dt is None:
        return default
    ts = pd.Timestamp(dt)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _range(
    start: datetime | None, end: datetime | None
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Parse to UTC and clamp to the available target window."""
    s = get_settings()
    lo = max(_utc(start, s.target_start), s.target_start)
    hi = min(_utc(end, s.target_end), s.target_end)
    if lo > hi:
        raise HTTPException(
            400,
            f"Empty range after clamping to available data "
            f"({s.target_start.isoformat()} .. {s.target_end.isoformat()}).",
        )
    return lo, hi


def range_params(
    start: Annotated[
        datetime | None, Query(description="ISO 8601; UTC if no offset")
    ] = None,
    end: Annotated[
        datetime | None, Query(description="ISO 8601; UTC if no offset")
    ] = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    return _range(start, end)


def selection_params(
    rng: Annotated[tuple[pd.Timestamp, pd.Timestamp], Depends(range_params)],
    mode: Literal["horizon", "decision"] = "horizon",
    horizon: Annotated[int, Query(ge=0, le=MAX_HORIZON_H)] = 4,
    cutoff: Annotated[str, Query(description="HH:MM UTC on D-1")] = "09:00",
) -> Params:
    m = CUTOFF_RE.match(cutoff)
    if not m:
        raise HTTPException(400, "cutoff must be HH:MM (24h, UTC)")
    return Params(rng[0], rng[1], mode, horizon, time(int(m[1]), int(m[2])))


def _series(p: Params) -> pd.DataFrame:
    store = get_store()
    return build_series(
        store.actuals, store.forecasts, p.start, p.end, p.mode, p.horizon, p.cutoff
    )


def _clean(v: object) -> object:
    if v is None or v is pd.NaT:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    return v


@router.get("/health", response_model=Health)
def health() -> Health:
    s = get_settings()
    store = get_store()
    return Health(
        status="ok",
        dataStart=s.target_start.to_pydatetime(),
        dataEnd=s.target_end.to_pydatetime(),
        actualRows=len(store.actuals),
        forecastRows=len(store.forecasts),
    )


@router.get("/series", response_model=list[SeriesPoint])
def series(p: Annotated[Params, Depends(selection_params)]) -> list[SeriesPoint]:
    df = _series(p)
    return [
        SeriesPoint(**{k: _clean(v) for k, v in row.items()})
        for row in df.to_dict(orient="records")
    ]


@router.get("/metrics", response_model=Metrics)
def summary(p: Annotated[Params, Depends(selection_params)]) -> Metrics:
    return Metrics(selection=p.selection, **metrics.summarize(_series(p)).to_dict())


@lru_cache(maxsize=64)
def _by_horizon(start: pd.Timestamp, end: pd.Timestamp) -> list[HorizonRow]:
    store = get_store()
    rows = metrics.by_horizon(store.actuals, store.forecasts, start, end)
    return [HorizonRow(**r) for r in rows]


@router.get("/metrics/by-horizon", response_model=list[HorizonRow])
def by_horizon(
    rng: Annotated[tuple[pd.Timestamp, pd.Timestamp], Depends(range_params)],
) -> list[HorizonRow]:
    return _by_horizon(*rng)


@router.get("/metrics/by-hour", response_model=list[HourRow])
def by_hour(p: Annotated[Params, Depends(selection_params)]) -> list[HourRow]:
    return [HourRow(**r) for r in metrics.by_hour(_series(p))]
