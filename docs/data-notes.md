# Elexon data notes

Verified on 2026-10-28 against `https://data.elexon.co.uk/bmrs/api/v1` (no API key needed).

## Endpoints and parameters

| Dataset | Endpoint | Filter params that work | Notes |
|---|---|---|---|
| Actuals | `/datasets/FUELHH/stream` | `settlementDateFrom`, `settlementDateTo` (dates, `YYYY-MM-DD`), or `publishDateTimeFrom`/`publishDateTimeTo`; `fuelType=WIND` filters server-side | We use `settlementDate*` + `fuelType=WIND`. |
| Forecasts | `/datasets/WINDFOR/stream` | `publishDateTimeFrom`, `publishDateTimeTo` (ISO 8601, `Z`) | Unknown params such as `startTimeFrom` and `from`/`to` are **silently ignored**, and the API then returns only the latest forecast. |

- `/stream` endpoints return a bare JSON array. The non-stream variant (`/datasets/WINDFOR?...`) wraps the rows in `{"data": [...]}`.
- **Max range:** no limit was hit. WINDFOR returned 90 days (52,560 rows) and FUELHH 40 days in a single request. The client still chunks requests into 7-day windows, to keep responses small and retries cheap.

## Fields

- FUELHH: `publishTime`, `startTime`, `settlementDate`, `settlementPeriod`, `fuelType`, `generation` (MW). `publishTime` is always `startTime + 30 min`.
- WINDFOR: `publishTime`, `startTime`, `generation` (MW).
- All timestamps are ISO 8601 UTC with a `Z` suffix, e.g. `2026-01-05T02:30:00Z`. Everything stays in UTC internally.

## Resolution and cadence

- **FUELHH is half-hourly.** For 2026-01-01 to 2026-02-02 there are 1,584 WIND rows, no duplicate `startTime` values, and no missing slots in the target range (2026-01-02 00:00Z to 2026-02-01 23:30Z).
- **WINDFOR is hourly** (`startTime` on the hour, 60-minute steps).
- **Publish cadence:** 8 runs per day at 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30 UTC. Gaps between runs are 2–4 h, and none is longer than 5 h. There is one irregular run at 12:25 instead of 11:30.
  Between 2025-12-30 and 2026-02-01 there are 272 runs (19,856 rows), with no duplicate `(publishTime, startTime)` pairs.
- **Reach:** each run has 73 hourly points, from 21:00 UTC on the day before publish to 21:00 UTC two days after publish. Horizons (`startTime − publishTime`) therefore run from about −10 h (backfilled/nowcast rows) to about +66 h.
  **Rows with a negative horizon exist and must be filtered out**, and so must rows beyond 48 h.

## Implications for the app

1. Join actuals to forecasts on exact `startTime`. Half-hour actual slots (`hh:30`) have no forecast and count as "no forecast" for coverage, unless we change the alignment.
   Default: **match timestamps only**, so coverage is measured over on-the-hour target times. See README → Assumptions.
2. With the default D-1 09:00 UTC cut-off, the selected run is **07:30 on D-1**. The 09:30 run lands just after the cut-off.
3. Value ranges in the fetch window: forecast 2,250–21,353 MW; actual 1,695–17,805 MW, mean 11,438 MW. The forecast maximum is well above the actual maximum.
   This is consistent with WINDFOR covering a slightly different fleet than metered FUELHH WIND (for example curtailment, or embedded wind). Expect a positive bias, and check it in the metrics.
