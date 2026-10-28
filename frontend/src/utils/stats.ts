import type { SeriesPoint } from "../types/api";

export interface Bin {
  /** inclusive lower edge, MW */
  from: number;
  /** exclusive upper edge, MW */
  to: number;
  count: number;
}

/** Histogram of values in fixed-width bins aligned to multiples of `width`. */
export function histogram(values: number[], width: number): Bin[] {
  if (values.length === 0 || width <= 0) return [];
  const lo = Math.floor(Math.min(...values) / width) * width;
  const hi = Math.floor(Math.max(...values) / width) * width;
  const bins: Bin[] = [];
  for (let from = lo; from <= hi; from += width)
    bins.push({ from, to: from + width, count: 0 });
  for (const v of values) {
    const bin = bins[Math.floor((v - lo) / width)];
    if (bin) bin.count += 1;
  }
  return bins;
}

/** Shortfall (actual - forecast) for points with both values. */
export function shortfalls(points: SeriesPoint[]): number[] {
  return points.flatMap((p) =>
    p.actual !== null && p.forecast !== null ? [p.actual - p.forecast] : [],
  );
}

function csvCell(v: string | number | null): string {
  if (v === null) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function toCsv(points: SeriesPoint[]): string {
  const cols: (keyof SeriesPoint)[] = [
    "startTime",
    "actual",
    "forecast",
    "error",
    "publishTime",
    "horizonHours",
  ];
  const lines = [cols.join(",")];
  for (const p of points) lines.push(cols.map((c) => csvCell(p[c])).join(","));
  return lines.join("\n") + "\n";
}
