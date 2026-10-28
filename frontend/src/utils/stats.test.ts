import { describe, expect, it } from "vitest";
import { histogram, shortfalls, toCsv } from "./stats";
import { rangeParams, selectionParams } from "../api/client";
import type { SeriesPoint } from "../types/api";

const point = (over: Partial<SeriesPoint>): SeriesPoint => ({
  startTime: "2026-01-10T00:00:00Z",
  actual: 100,
  forecast: 120,
  error: 20,
  publishTime: "2026-01-09T18:30:00Z",
  horizonHours: 5.5,
  ...over,
});

describe("histogram", () => {
  it("bins values into aligned fixed-width buckets", () => {
    const bins = histogram([-750, -10, 0, 499, 500, 1200], 500);
    expect(bins.map((b) => [b.from, b.count])).toEqual([
      [-1000, 1],
      [-500, 1],
      [0, 2],
      [500, 1],
      [1000, 1],
    ]);
  });

  it("returns no bins for empty input", () => {
    expect(histogram([], 500)).toEqual([]);
  });
});

describe("shortfalls", () => {
  it("skips points missing either side", () => {
    const pts = [point({}), point({ forecast: null }), point({ actual: null })];
    expect(shortfalls(pts)).toEqual([-20]);
  });
});

describe("toCsv", () => {
  it("writes a header and blanks for nulls", () => {
    const csv = toCsv([point({ forecast: null, error: null, publishTime: null })]);
    expect(csv).toBe(
      "startTime,actual,forecast,error,publishTime,horizonHours\n" +
        "2026-01-10T00:00:00Z,100,,,,5.5\n",
    );
  });
});

describe("query params", () => {
  it("uses inclusive whole-day UTC ranges", () => {
    expect(
      rangeParams({ startDate: "2026-01-05", endDate: "2026-01-06" }).toString(),
    ).toBe("start=2026-01-05T00%3A00%3A00Z&end=2026-01-06T23%3A30%3A00Z");
  });

  it("sends only the parameter relevant to the mode", () => {
    const base = {
      startDate: "2026-01-05",
      endDate: "2026-01-06",
      horizon: 4,
      cutoff: "09:00",
    };
    const h = selectionParams({ ...base, mode: "horizon" });
    expect(h.get("horizon")).toBe("4");
    expect(h.has("cutoff")).toBe(false);
    const d = selectionParams({ ...base, mode: "decision" });
    expect(d.get("cutoff")).toBe("09:00");
    expect(d.has("horizon")).toBe(false);
  });
});
