import { describe, expect, it } from "vitest";
import { DEFAULT_QUERY, parseQuery, serializeQuery } from "./query";

describe("URL query state", () => {
  it("round-trips a decision-mode selection", () => {
    const q = { ...DEFAULT_QUERY, mode: "decision" as const, cutoff: "11:30" };
    expect(parseQuery(serializeQuery(q))).toEqual(q);
  });

  it("falls back to defaults for invalid or out-of-range values", () => {
    expect(
      parseQuery("?start=2025-12-01&end=bad&mode=x&horizon=99&cutoff=25:00"),
    ).toEqual(DEFAULT_QUERY);
  });

  it("rejects an end date before the start date", () => {
    const q = parseQuery("?start=2026-01-20&end=2026-01-10");
    expect(q.startDate).toBe("2026-01-20");
    expect(q.endDate).toBe(DEFAULT_QUERY.endDate);
  });
});
