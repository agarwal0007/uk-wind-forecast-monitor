from datetime import time

import numpy as np
import pandas as pd
import pytest

from app.core.selection import (
    build_series,
    decision_cutoffs,
    horizon_cutoffs,
    select_forecasts,
    target_grid,
)


def ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


def fc(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    """Forecast frame from (startTime, publishTime, forecast) tuples."""
    return pd.DataFrame(
        {
            "startTime": [ts(r[0]) for r in rows],
            "publishTime": [ts(r[1]) for r in rows],
            "forecast": [float(r[2]) for r in rows],
        }
    )


def act(rows: list[tuple[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {"startTime": [ts(r[0]) for r in rows], "actual": [float(r[1]) for r in rows]}
    )


T = "2026-01-10T12:00"


def select_one(forecasts: pd.DataFrame, horizon_h: float, target: str = T) -> pd.Series:
    targets = pd.DatetimeIndex([ts(target)], name="startTime")
    return select_forecasts(forecasts, horizon_cutoffs(targets, horizon_h)).iloc[0]


def test_latest_publish_before_cutoff_is_selected() -> None:
    f = fc(
        [
            (T, "2026-01-10T02:30", 100),
            (T, "2026-01-10T04:30", 200),  # latest with publishTime <= T-4h = 08:00
            (T, "2026-01-10T09:30", 300),  # after cutoff: excluded
        ]
    )
    row = select_one(f, 4)
    assert row["forecast"] == 200
    assert row["publishTime"] == ts("2026-01-10T04:30")
    assert row["horizonHours"] == 7.5


def test_publish_exactly_at_cutoff_is_included() -> None:
    f = fc([(T, "2026-01-10T07:00", 100), (T, "2026-01-10T08:00", 200)])
    assert select_one(f, 4)["forecast"] == 200


def test_forecast_published_after_cutoff_excluded() -> None:
    f = fc([(T, "2026-01-10T08:01", 100)])
    assert np.isnan(select_one(f, 4)["forecast"])


def test_tie_on_publish_time_last_row_wins() -> None:
    f = fc([(T, "2026-01-10T04:30", 100), (T, "2026-01-10T04:30", 150)])
    assert select_one(f, 4)["forecast"] == 150


def test_horizon_zero_boundary() -> None:
    f = fc([(T, T, 500), (T, "2026-01-10T11:00", 400)])
    row = select_one(f, 0)
    assert row["forecast"] == 500
    assert row["horizonHours"] == 0


def test_negative_horizon_rows_excluded() -> None:
    # Published after the target time (backfilled): never a valid forecast.
    f = fc([(T, "2026-01-10T13:00", 500)])
    assert np.isnan(select_one(f, 0)["forecast"])


def test_no_forecast_available_is_missing_not_filled() -> None:
    f = fc([("2026-01-10T13:00", "2026-01-10T02:30", 100)])  # different target
    row = select_one(f, 4)
    assert np.isnan(row["forecast"])
    assert pd.isna(row["publishTime"])


def test_horizons_over_48h_excluded() -> None:
    # Only candidate is 49h old: excluded even though it's before the cutoff.
    f = fc([(T, "2026-01-08T11:00", 100)])
    assert np.isnan(select_one(f, 4)["forecast"])
    # Exactly 48h is allowed.
    f = fc([(T, "2026-01-08T12:00", 100)])
    assert select_one(f, 48)["forecast"] == 100


def test_does_not_fall_back_to_older_than_48h_when_recent_missing() -> None:
    f = fc([(T, "2026-01-08T10:00", 100), (T, "2026-01-10T10:00", 999)])
    # H=4 -> cutoff 08:00; 10:00 run excluded; 50h-old run excluded by horizon cap.
    assert np.isnan(select_one(f, 4)["forecast"])


def test_target_grid_is_hourly_and_inclusive() -> None:
    grid = target_grid(ts("2026-01-02T00:30"), ts("2026-01-02T03:00"))
    assert list(grid) == [
        ts("2026-01-02T01:00"),
        ts("2026-01-02T02:00"),
        ts("2026-01-02T03:00"),
    ]


def test_decision_cutoffs_across_day_boundary() -> None:
    targets = pd.DatetimeIndex([ts("2026-01-10T23:00"), ts("2026-01-11T00:00")])
    cut = decision_cutoffs(targets, time(9, 0))
    assert list(cut) == [ts("2026-01-09T09:00"), ts("2026-01-10T09:00")]


def test_decision_mode_uses_d_minus_1_cutoff() -> None:
    f = fc(
        [
            # Targets on 2026-01-10 (D) and 2026-01-11 (D+1)
            ("2026-01-10T23:00", "2026-01-09T07:30", 10),  # D-1 07:30: picked
            ("2026-01-10T23:00", "2026-01-09T09:30", 11),  # after D-1 09:00 cut-off
            ("2026-01-10T23:00", "2026-01-10T07:30", 12),  # day D: too late
            ("2026-01-11T00:00", "2026-01-09T07:30", 20),
            ("2026-01-11T00:00", "2026-01-10T07:30", 21),  # D-1 for the 11th: picked
            ("2026-01-11T00:00", "2026-01-10T09:30", 22),
        ]
    )
    a = act([("2026-01-10T23:00", 9), ("2026-01-11T00:00", 25)])
    s = build_series(
        a, f, ts("2026-01-10T23:00"), ts("2026-01-11T00:00"), "decision", cutoff=time(9)
    )
    assert s["forecast"].tolist() == [10, 21]
    assert s["horizonHours"].tolist() == [39.5, 16.5]
    assert s["error"].tolist() == [1, -4]


def test_missing_actuals_kept_as_gap() -> None:
    f = fc(
        [
            ("2026-01-10T12:00", "2026-01-10T07:30", 100),
            ("2026-01-10T13:00", "2026-01-10T07:30", 110),
        ]
    )
    a = act([("2026-01-10T12:00", 90)])  # 13:00 actual missing
    s = build_series(a, f, ts("2026-01-10T12:00"), ts("2026-01-10T13:00"), "horizon", 4)
    assert s["actual"].isna().tolist() == [False, True]
    assert s["forecast"].tolist() == [100, 110]
    assert s["error"].iloc[0] == 10
    assert np.isnan(s["error"].iloc[1])


def test_half_hour_actuals_not_aligned_to_hourly_forecasts() -> None:
    f = fc([("2026-01-10T12:00", "2026-01-10T07:30", 100)])
    a = act([("2026-01-10T12:00", 90), ("2026-01-10T12:30", 95)])
    s = build_series(a, f, ts("2026-01-10T12:00"), ts("2026-01-10T12:30"), "horizon", 4)
    assert len(s) == 1  # only on-the-hour targets are evaluated


@pytest.mark.parametrize(
    "h,expected", [(0, 3), (1, 3), (2, 2), (5, 1), (4, 2), (8, 1), (9, None)]
)
def test_horizon_slider_moves_selection(h: int, expected: float | None) -> None:
    f = fc(
        [
            (T, "2026-01-10T04:00", 1),
            (T, "2026-01-10T08:00", 2),
            (T, "2026-01-10T11:00", 3),
        ]
    )
    got = select_one(f, h)["forecast"]
    if expected is None:
        assert np.isnan(got)  # cutoff 03:00 precedes every run
    else:
        assert got == expected
