export type Mode = "horizon" | "decision";

export interface SeriesPoint {
  startTime: string;
  actual: number | null;
  forecast: number | null;
  /** forecast - actual (positive = over-forecast) */
  error: number | null;
  publishTime: string | null;
  horizonHours: number | null;
}

export interface Selection {
  start: string;
  end: string;
  mode: Mode;
  horizon: number | null;
  cutoff: string | null;
}

export interface Metrics {
  selection: Selection;
  targets: number;
  withForecast: number;
  paired: number;
  coveragePct: number | null;
  meanActual: number | null;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  nmaePct: number | null;
  /** Percentiles of (actual - forecast) */
  p10: number | null;
  p50: number | null;
  p90: number | null;
}

export interface HorizonRow {
  horizon: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  p10: number | null;
  p90: number | null;
  coveragePct: number | null;
  paired: number;
}

export interface HourRow {
  hour: number;
  mae: number | null;
  bias: number | null;
  n: number;
}

export interface Health {
  status: "ok";
  dataStart: string;
  dataEnd: string;
  actualRows: number;
  forecastRows: number;
}

export interface Query {
  /** YYYY-MM-DD, inclusive */
  startDate: string;
  /** YYYY-MM-DD, inclusive */
  endDate: string;
  mode: Mode;
  horizon: number;
  /** HH:MM UTC on D-1 */
  cutoff: string;
}
