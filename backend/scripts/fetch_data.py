"""Fetch January-2026 wind actuals and forecasts from Elexon into backend/data/.

Usage (from backend/):  python -m scripts.fetch_data
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.core.data_store import ACTUALS_FILE, FORECASTS_FILE, write_json  # noqa: E402
from app.ingest.elexon import ElexonClient  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    client = ElexonClient(settings.elexon_base_url)

    actuals = client.fetch_actuals(
        settings.target_start.date(), settings.target_end.date()
    )
    forecasts = client.fetch_forecasts(
        settings.publish_start.date(), settings.target_end.date()
    )

    write_json(actuals, settings.data_dir / ACTUALS_FILE)
    write_json(forecasts, settings.data_dir / FORECASTS_FILE)
    meta = {
        "fetchedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": settings.elexon_base_url,
        "actualRows": len(actuals),
        "forecastRows": len(forecasts),
        "forecastRuns": int(forecasts["publishTime"].nunique()),
    }
    (settings.data_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(f"actuals:   {len(actuals):>6} rows  "
          f"{actuals.startTime.min()} -> {actuals.startTime.max()}")
    print(f"forecasts: {len(forecasts):>6} rows  "
          f"published {forecasts.publishTime.min()} -> {forecasts.publishTime.max()}  "
          f"({meta['forecastRuns']} runs)")
    print("\nsample actuals:\n", actuals.head(3).to_string(index=False))
    print("\nsample forecasts:\n", forecasts.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
