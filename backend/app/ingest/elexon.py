"""Minimal client for the Elexon Insights API (FUELHH actuals, WINDFOR forecasts).

See docs/data-notes.md for the verified parameter names and data shapes.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import httpx
import pandas as pd

log = logging.getLogger(__name__)

CHUNK_DAYS = 7
RETRY_STATUSES = {429, 500, 502, 503, 504}


class ElexonError(RuntimeError):
    pass


class ElexonClient:
    def __init__(
        self,
        base_url: str = "https://data.elexon.co.uk/bmrs/api/v1",
        timeout: float = 60.0,
        max_retries: int = 4,
        backoff_seconds: float = 1.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self._client = client or httpx.Client(timeout=timeout)

    def _get(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.get(url, params=params)
                if resp.status_code in RETRY_STATUSES:
                    raise httpx.HTTPStatusError(
                        f"retryable status {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                resp.raise_for_status()
                data = resp.json()
                # /stream returns a bare list; non-stream wraps it in {"data": [...]}.
                return data["data"] if isinstance(data, dict) else data
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status is not None and status not in RETRY_STATUSES:
                    raise ElexonError(f"GET {url} failed: {status}") from exc
                if attempt == self.max_retries:
                    raise ElexonError(f"GET {url} failed after retries: {exc}") from exc
                wait = self.backoff_seconds * 2**attempt
                log.warning("GET %s failed (%s); retrying in %.1fs", url, exc, wait)
                time.sleep(wait)
        raise AssertionError("unreachable")

    def fetch_actuals(self, start: date, end: date) -> pd.DataFrame:
        """Half-hourly WIND outturn for settlement dates start..end (inclusive)."""
        rows: list[dict[str, Any]] = []
        for chunk_start, chunk_end in _date_chunks(start, end):
            rows += self._get(
                "/datasets/FUELHH/stream",
                {
                    "settlementDateFrom": chunk_start.isoformat(),
                    "settlementDateTo": chunk_end.isoformat(),
                    "fuelType": "WIND",
                },
            )
        df = pd.DataFrame(rows, columns=["startTime", "fuelType", "generation"])
        df = df[df["fuelType"] == "WIND"]
        df = df.rename(columns={"generation": "actual"})[["startTime", "actual"]]
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
        df["actual"] = df["actual"].astype(float)
        return (
            df.drop_duplicates("startTime", keep="last")
            .sort_values("startTime")
            .reset_index(drop=True)
        )

    def fetch_forecasts(self, publish_from: date, publish_to: date) -> pd.DataFrame:
        """Hourly WINDFOR forecasts published on dates publish_from..publish_to."""
        rows: list[dict[str, Any]] = []
        for chunk_start, chunk_end in _date_chunks(publish_from, publish_to):
            rows += self._get(
                "/datasets/WINDFOR/stream",
                {
                    "publishDateTimeFrom": f"{chunk_start.isoformat()}T00:00:00Z",
                    "publishDateTimeTo": f"{chunk_end.isoformat()}T23:59:59Z",
                },
            )
        df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
        df = df.rename(columns={"generation": "forecast"})
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
        df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
        df["forecast"] = df["forecast"].astype(float)
        return (
            df.drop_duplicates(["publishTime", "startTime"], keep="last")
            .sort_values(["publishTime", "startTime"])
            .reset_index(drop=True)
        )


def _date_chunks(start: date, end: date) -> Iterator[tuple[date, date]]:
    """Split start..end (inclusive) into non-overlapping CHUNK_DAYS windows."""
    if end < start:
        raise ValueError("end must not be before start")
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=CHUNK_DAYS - 1), end)
        yield cur, chunk_end
        cur = chunk_end + timedelta(days=1)
