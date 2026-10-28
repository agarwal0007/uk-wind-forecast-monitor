import math

import numpy as np
import pandas as pd
import pytest

from app.core.metrics import by_horizon, by_hour, summarize


def series(rows: list[tuple[str, float | None, float | None]]) -> pd.DataFrame:
    """Aligned series from (startTime, actual, forecast) tuples."""
    df = pd.DataFrame(
        {
            "startTime": [pd.Timestamp(r[0], tz="UTC") for r in rows],
            "actual": [np.nan if r[1] is None else r[1] for r in rows],
            "forecast": [np.nan if r[2] is None else r[2] for r in rows],
        }
    )
    df["error"] = df["forecast"] - df["actual"]
    return df


def test_summary_basic_metrics() -> None:
    s = series(
        [
            ("2026-01-10T00:00", 100, 110),  # err +10
            ("2026-01-10T01:00", 100, 80),  # err -20
            ("2026-01-10T02:00", 200, 230),  # err +30
            ("2026-01-10T03:00", 200, 200),  # err 0
        ]
    )
    m = summarize(s)
    assert m.paired == 4
    assert m.mae == 15
    assert m.bias == 5
    assert m.rmse == pytest.approx(math.sqrt((100 + 400 + 900 + 0) / 4), abs=0.01)
    assert m.meanActual == 150
    assert m.nmaePct == 10
    # Percentiles of (actual - forecast) = [-10, 20, -30, 0]
    assert m.p50 == pytest.approx(np.percentile([-10, 20, -30, 0], 50))
    assert m.p10 == pytest.approx(np.percentile([-10, 20, -30, 0], 10))
    assert m.p10 < 0 < m.p90
    assert m.coveragePct == 100


def test_positive_bias_means_over_forecast() -> None:
    m = summarize(
        series([("2026-01-10T00:00", 100, 150), ("2026-01-10T01:00", 100, 150)])
    )
    assert m.bias == 50
    assert m.p10 == -50  # wind came in 50 MW below forecast


def test_coverage_and_missing_values() -> None:
    s = series(
        [
            ("2026-01-10T00:00", 100, 110),
            ("2026-01-10T01:00", 100, None),  # no forecast
            ("2026-01-10T02:00", None, 120),  # no actual
            ("2026-01-10T03:00", 100, None),
        ]
    )
    m = summarize(s)
    assert m.targets == 4
    assert m.withForecast == 2
    assert m.coveragePct == 50
    assert m.paired == 1
    assert m.mae == 10


def test_empty_and_all_missing_return_none() -> None:
    m = summarize(series([("2026-01-10T00:00", 100, None)]))
    assert m.paired == 0 and m.mae is None and m.p10 is None
    assert m.coveragePct == 0
    empty = summarize(series([]))
    assert empty.targets == 0 and empty.coveragePct is None


def test_nmae_none_when_mean_actual_zero() -> None:
    m = summarize(series([("2026-01-10T00:00", 0, 10)]))
    assert m.mae == 10 and m.nmaePct is None


def test_by_hour_groups_on_utc_hour() -> None:
    s = series(
        [
            ("2026-01-10T05:00", 100, 110),
            ("2026-01-11T05:00", 100, 70),
            ("2026-01-10T06:00", 100, None),
        ]
    )
    rows = by_hour(s)
    assert len(rows) == 24
    assert rows[5] == {"hour": 5, "mae": 20, "bias": -10, "n": 2}
    assert rows[6] == {"hour": 6, "mae": None, "bias": None, "n": 0}


def test_by_horizon_uses_selection_per_horizon() -> None:
    t = pd.Timestamp("2026-01-10T12:00", tz="UTC")
    forecasts = pd.DataFrame(
        {
            "startTime": [t, t],
            "publishTime": [t - pd.Timedelta(hours=10), t - pd.Timedelta(hours=1)],
            "forecast": [150.0, 105.0],
        }
    )
    actuals = pd.DataFrame({"startTime": [t], "actual": [100.0]})
    rows = by_horizon(actuals, forecasts, t, t, range(0, 12))
    mae = {r["horizon"]: r["mae"] for r in rows}
    assert mae[0] == 5 and mae[1] == 5  # 1h-old run
    assert mae[2] == 50 and mae[10] == 50  # 10h-old run
    assert mae[11] is None  # nothing old enough
