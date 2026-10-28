"""API tests against the committed January-2026 cache."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["actualRows"] > 0 and body["forecastRows"] > 0


def test_series_horizon_mode_shape() -> None:
    r = client.get(
        "/api/series",
        params={"start": "2026-01-10T00:00Z", "end": "2026-01-10T23:00Z", "horizon": 4},
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 24
    first = rows[0]
    assert set(first) == {
        "startTime",
        "actual",
        "forecast",
        "error",
        "publishTime",
        "horizonHours",
    }
    for row in rows:
        if row["forecast"] is not None:
            assert row["horizonHours"] >= 4


def test_series_decision_mode_uses_previous_day() -> None:
    r = client.get(
        "/api/series",
        params={
            "start": "2026-01-10T00:00Z",
            "end": "2026-01-10T23:00Z",
            "mode": "decision",
            "cutoff": "09:00",
        },
    )
    assert r.status_code == 200
    for row in r.json():
        assert row["publishTime"] is None or row["publishTime"] <= "2026-01-09T09:00"


def test_metrics_and_clamping() -> None:
    r = client.get("/api/metrics", params={"start": "2025-06-01", "end": "2027-01-01"})
    assert r.status_code == 200
    m = r.json()
    assert m["selection"]["start"].startswith("2026-01-02T00:00")
    assert m["selection"]["end"].startswith("2026-02-01T23:30")
    assert m["targets"] == 31 * 24
    assert m["mae"] > 0


def test_by_horizon_and_by_hour() -> None:
    params = {"start": "2026-01-05", "end": "2026-01-12"}
    hz = client.get("/api/metrics/by-horizon", params=params).json()
    assert [r["horizon"] for r in hz] == list(range(49))
    hr = client.get("/api/metrics/by-hour", params=params).json()
    assert [r["hour"] for r in hr] == list(range(24))


def test_validation_errors() -> None:
    assert client.get("/api/series", params={"horizon": 49}).status_code == 422
    assert client.get("/api/series", params={"mode": "bogus"}).status_code == 422
    assert (
        client.get(
            "/api/series", params={"mode": "decision", "cutoff": "9am"}
        ).status_code
        == 400
    )
    assert client.get("/api/series", params={"start": "not-a-date"}).status_code == 422
    r = client.get("/api/series", params={"start": "2026-01-20", "end": "2026-01-10"})
    assert r.status_code == 400
