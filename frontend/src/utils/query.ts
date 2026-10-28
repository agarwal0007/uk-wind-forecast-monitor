import type { Query } from "../types/api";

export const DATA_START = "2026-01-02";
export const DATA_END = "2026-02-01";

export const DEFAULT_QUERY: Query = {
  startDate: DATA_START,
  endDate: DATA_END,
  mode: "horizon",
  horizon: 4,
  cutoff: "09:00",
};

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;

/** Read a Query from URL search params, falling back to defaults for bad values. */
export function parseQuery(search: string): Query {
  const p = new URLSearchParams(search);
  const q = { ...DEFAULT_QUERY };
  const start = p.get("start");
  const end = p.get("end");
  if (start && DATE_RE.test(start) && start >= DATA_START && start <= DATA_END)
    q.startDate = start;
  if (end && DATE_RE.test(end) && end >= q.startDate && end <= DATA_END) q.endDate = end;
  const mode = p.get("mode");
  if (mode === "horizon" || mode === "decision") q.mode = mode;
  const h = Number(p.get("horizon"));
  if (p.has("horizon") && Number.isInteger(h) && h >= 0 && h <= 48) q.horizon = h;
  const cutoff = p.get("cutoff");
  if (cutoff && TIME_RE.test(cutoff)) q.cutoff = cutoff;
  return q;
}

export function serializeQuery(q: Query): string {
  const p = new URLSearchParams({ start: q.startDate, end: q.endDate, mode: q.mode });
  if (q.mode === "horizon") p.set("horizon", String(q.horizon));
  else p.set("cutoff", q.cutoff);
  return `?${p.toString()}`;
}
