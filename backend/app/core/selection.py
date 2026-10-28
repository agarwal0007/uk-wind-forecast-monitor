"""Forecast selection: which forecast was "live" for each target time.

Rule: for target time T with cut-off C(T), the selected forecast is the one with
the latest publishTime such that publishTime <= C(T), restricted to forecasts
whose horizon (startTime - publishTime) is within [0, MAX_HORIZON_H] hours.

- Horizon mode:        C(T) = T - H
- Decision-time mode:  C(T) = (date of T) - 1 day + cut-off time-of-day (UTC)

If no forecast qualifies, the target is left as missing (NaN) - never filled.
Pure functions only: no I/O.
"""

from __future__ import annotations

from datetime import time
from typing import Literal

import pandas as pd

MAX_HORIZON_H = 48
Mode = Literal["horizon", "decision"]

SERIES_COLUMNS = [
    "startTime",
    "actual",
    "forecast",
    "error",
    "publishTime",
    "horizonHours",
]


def target_grid(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """On-the-hour target times in [start, end].

    WINDFOR is hourly, so we evaluate on the hour only (actuals are matched on
    exact timestamps; the :30 actual slots have no forecast to compare against).
    """
    return pd.date_range(start.ceil("1h"), end, freq="1h", name="startTime")


def horizon_cutoffs(targets: pd.DatetimeIndex, horizon_h: float) -> pd.Series:
    return pd.Series(targets - pd.Timedelta(hours=horizon_h), index=targets)


def decision_cutoffs(targets: pd.DatetimeIndex, cutoff: time) -> pd.Series:
    offset = pd.Timedelta(hours=cutoff.hour, minutes=cutoff.minute)
    return pd.Series(targets.normalize() - pd.Timedelta(days=1) + offset, index=targets)


def select_forecasts(forecasts: pd.DataFrame, cutoffs: pd.Series) -> pd.DataFrame:
    """Pick the latest-published eligible forecast for each target in `cutoffs`.

    `forecasts` has columns startTime, publishTime, forecast. `cutoffs` is indexed
    by target time. Returns one row per target (forecast/publishTime NaN if none).
    Ties on publishTime for the same startTime are broken by input order (last
    row wins), matching how the ingest layer de-duplicates.
    """
    fc = forecasts[["startTime", "publishTime", "forecast"]].copy()
    fc["_order"] = range(len(fc))
    horizon = (fc["startTime"] - fc["publishTime"]) / pd.Timedelta(hours=1)
    fc = fc[(horizon >= 0) & (horizon <= MAX_HORIZON_H)]

    targets = pd.DataFrame({"startTime": cutoffs.index, "cutoff": cutoffs.to_numpy()})
    cand = targets.merge(fc, on="startTime", how="inner")
    cand = cand[cand["publishTime"] <= cand["cutoff"]]
    chosen = (
        cand.sort_values(["publishTime", "_order"])
        .groupby("startTime", sort=False)
        .tail(1)
        .set_index("startTime")
    )
    out = chosen.reindex(cutoffs.index)[["forecast", "publishTime"]]
    out["horizonHours"] = (out.index - out["publishTime"]) / pd.Timedelta(hours=1)
    return out


def build_series(
    actuals: pd.DataFrame,
    forecasts: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    mode: Mode = "horizon",
    horizon_h: float = 4,
    cutoff: time = time(9, 0),
) -> pd.DataFrame:
    """Aligned actual vs selected-forecast series for on-the-hour targets.

    error = forecast - actual (positive = over-forecast). NaN where either side
    is missing.
    """
    targets = target_grid(start, end)
    if mode == "horizon":
        cutoffs = horizon_cutoffs(targets, horizon_h)
    else:
        cutoffs = decision_cutoffs(targets, cutoff)

    selected = select_forecasts(forecasts, cutoffs)
    act = actuals.drop_duplicates("startTime", keep="last").set_index("startTime")
    selected["actual"] = act["actual"].reindex(targets)
    selected["error"] = selected["forecast"] - selected["actual"]
    return selected.reset_index()[SERIES_COLUMNS]
