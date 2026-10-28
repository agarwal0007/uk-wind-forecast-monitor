import type { HorizonRow, HourRow, Metrics, Query, SeriesPoint } from "../types/api";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function get<T>(
  path: string,
  params: URLSearchParams,
  signal?: AbortSignal,
): Promise<T> {
  const res = await fetch(`${BASE}/api/${path}?${params.toString()}`, { signal });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (body.detail) detail = JSON.stringify(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(`${res.status}: ${detail}`, res.status);
  }
  return (await res.json()) as T;
}

export function rangeParams(q: Pick<Query, "startDate" | "endDate">): URLSearchParams {
  return new URLSearchParams({
    start: `${q.startDate}T00:00:00Z`,
    end: `${q.endDate}T23:30:00Z`,
  });
}

export function selectionParams(q: Query): URLSearchParams {
  const p = rangeParams(q);
  p.set("mode", q.mode);
  if (q.mode === "horizon") p.set("horizon", String(q.horizon));
  else p.set("cutoff", q.cutoff);
  return p;
}

export const api = {
  series: (q: Query, s?: AbortSignal) =>
    get<SeriesPoint[]>("series", selectionParams(q), s),
  metrics: (q: Query, s?: AbortSignal) => get<Metrics>("metrics", selectionParams(q), s),
  byHour: (q: Query, s?: AbortSignal) =>
    get<HourRow[]>("metrics/by-hour", selectionParams(q), s),
  byHorizon: (q: Pick<Query, "startDate" | "endDate">, s?: AbortSignal) =>
    get<HorizonRow[]>("metrics/by-horizon", rangeParams(q), s),
};
