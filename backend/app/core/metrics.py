"""Forecast accuracy metrics over an aligned series (see selection.build_series).

Sign conventions:
- bias = mean(forecast - actual); positive = over-forecast (under-buying risk).
- percentiles are of (actual - forecast); P10 < 0 means "in 90% of periods wind
  came in no more than |P10| MW below forecast", i.e. the safety margin.
Pure functions only: no I/O.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from app.core.selection import MAX_HORIZON_H, build_series


@dataclass(frozen=True)
class Summary:
    targets: int  # target times in range
    withForecast: int  # targets that have a selected forecast
    paired: int  # targets with both forecast and actual (metrics use these)
    coveragePct: float | None  # withForecast / targets * 100
    meanActual: float | None
    mae: float | None
    rmse: float | None
    bias: float | None
    nmaePct: float | None  # MAE / mean(actual) * 100
    p10: float | None
    p50: float | None
    p90: float | None

    def to_dict(self) -> dict[str, float | int | None]:
        return asdict(self)


def _f(x: float | np.floating) -> float:
    return float(round(float(x), 2))


def summarize(series: pd.DataFrame) -> Summary:
    targets = len(series)
    with_fc = int(series["forecast"].notna().sum())
    paired = series.dropna(subset=["forecast", "actual"])
    coverage = _f(with_fc / targets * 100) if targets else None
    if paired.empty:
        return Summary(targets, with_fc, 0, coverage, *([None] * 8))

    err = paired["forecast"] - paired["actual"]  # + = over-forecast
    shortfall = -err  # actual - forecast
    mean_actual = paired["actual"].mean()
    mae = err.abs().mean()
    p10, p50, p90 = np.percentile(shortfall, [10, 50, 90])
    return Summary(
        targets=targets,
        withForecast=with_fc,
        paired=len(paired),
        coveragePct=coverage,
        meanActual=_f(mean_actual),
        mae=_f(mae),
        rmse=_f(np.sqrt((err**2).mean())),
        bias=_f(err.mean()),
        nmaePct=_f(mae / mean_actual * 100) if mean_actual > 0 else None,
        p10=_f(p10),
        p50=_f(p50),
        p90=_f(p90),
    )


def by_horizon(
    actuals: pd.DataFrame,
    forecasts: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    horizons: range = range(0, MAX_HORIZON_H + 1),
) -> list[dict[str, float | int | None]]:
    rows: list[dict[str, float | int | None]] = []
    for h in horizons:
        s = summarize(build_series(actuals, forecasts, start, end, "horizon", h))
        rows.append(
            {
                "horizon": h,
                "mae": s.mae,
                "rmse": s.rmse,
                "bias": s.bias,
                "p10": s.p10,
                "p90": s.p90,
                "coveragePct": s.coveragePct,
                "paired": s.paired,
            }
        )
    return rows


def by_hour(series: pd.DataFrame) -> list[dict[str, float | int | None]]:
    """MAE and bias by UTC hour of day (0..23); empty hours return None."""
    paired = series.dropna(subset=["forecast", "actual"])
    err = paired["forecast"] - paired["actual"]
    hours = paired["startTime"].dt.hour
    grouped = pd.DataFrame({"hour": hours, "err": err}).groupby("hour")["err"]
    mae = grouped.apply(lambda e: e.abs().mean())
    bias = grouped.mean()
    count = grouped.size()
    return [
        {
            "hour": h,
            "mae": _f(mae[h]) if h in mae.index else None,
            "bias": _f(bias[h]) if h in bias.index else None,
            "n": int(count[h]) if h in count.index else 0,
        }
        for h in range(24)
    ]
