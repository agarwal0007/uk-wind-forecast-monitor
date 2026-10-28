import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { HourRow } from "../types/api";
import { gw, mw } from "../utils/format";

export function HourChart({ rows }: { rows: HourRow[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis
          dataKey="hour"
          tickFormatter={(h: number) => `${String(h).padStart(2, "0")}`}
          stroke="var(--axis)"
          tick={{ fontSize: 12 }}
          interval={2}
        />
        <YAxis
          tickFormatter={gw}
          stroke="var(--axis)"
          tick={{ fontSize: 12 }}
          width={56}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
          }}
          labelFormatter={(h: number) => `${String(h).padStart(2, "0")}:00 UTC`}
          formatter={(v: number, name: string) => [mw(v), name]}
        />
        <Bar
          dataKey="mae"
          name="MAE"
          fill="var(--c-forecast)"
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
