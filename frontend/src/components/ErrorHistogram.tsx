import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SeriesPoint } from "../types/api";
import { histogram, shortfalls } from "../utils/stats";
import { mw } from "../utils/format";

const BIN_MW = 500;

interface Props {
  points: SeriesPoint[];
  p10: number | null;
}

export function ErrorHistogram({ points, p10 }: Props) {
  const bins = useMemo(
    () =>
      histogram(shortfalls(points), BIN_MW).map((b) => ({
        ...b,
        mid: b.from + BIN_MW / 2,
      })),
    [points],
  );
  const ticks = useMemo(() => {
    if (bins.length === 0) return [];
    const lo = Math.floor((bins[0]?.from ?? 0) / 2000) * 2000;
    const hi = Math.ceil((bins[bins.length - 1]?.to ?? 0) / 2000) * 2000;
    return Array.from({ length: (hi - lo) / 2000 + 1 }, (_, i) => lo + i * 2000);
  }, [bins]);
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart
        data={bins}
        margin={{ top: 20, right: 12, bottom: 8, left: 0 }}
        barCategoryGap={1}
      >
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis
          dataKey="mid"
          type="number"
          domain={[ticks[0] ?? 0, ticks[ticks.length - 1] ?? 0]}
          ticks={ticks}
          tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}`}
          stroke="var(--axis)"
          tick={{ fontSize: 12 }}
          label={{
            value: "actual − forecast (GW)",
            position: "insideBottom",
            offset: -6,
            fontSize: 12,
            fill: "var(--muted)",
          }}
          height={40}
        />
        <YAxis
          stroke="var(--axis)"
          tick={{ fontSize: 12 }}
          width={40}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
          }}
          labelFormatter={(mid: number) =>
            `${mw(mid - BIN_MW / 2)} to ${mw(mid + BIN_MW / 2)}`
          }
          formatter={(v: number) => [`${v} hours`, "Count"]}
        />
        <ReferenceLine x={0} stroke="var(--axis)" />
        {p10 !== null && (
          <ReferenceLine
            x={p10}
            stroke="var(--c-margin)"
            strokeDasharray="4 4"
            label={{
              value: "P10",
              fill: "var(--c-margin)",
              fontSize: 12,
              position: "top",
            }}
          />
        )}
        <Bar dataKey="count" fill="var(--c-forecast)" isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
