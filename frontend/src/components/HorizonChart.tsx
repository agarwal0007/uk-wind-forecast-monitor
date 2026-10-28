import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { HorizonRow } from "../types/api";
import { gw, mw, pct } from "../utils/format";

interface Props {
  rows: HorizonRow[];
  current: number | null;
}

export function HorizonChart({ rows, current }: Props) {
  const data = rows.map((r) => ({ ...r, margin: r.p10 === null ? null : -r.p10 }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis
          dataKey="horizon"
          type="number"
          domain={[0, 48]}
          ticks={[0, 6, 12, 18, 24, 30, 36, 42, 48]}
          tickFormatter={(h: number) => `${h}h`}
          stroke="var(--axis)"
          tick={{ fontSize: 12 }}
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
          labelFormatter={(h) => {
            const r = rows.find((x) => x.horizon === h);
            return `${h} h ahead · coverage ${pct(r?.coveragePct)}`;
          }}
          formatter={(v: number) => mw(v)}
        />
        <Legend wrapperStyle={{ fontSize: 13 }} />
        {current !== null && (
          <ReferenceLine x={current} stroke="var(--axis)" strokeDasharray="4 4" />
        )}
        <Line
          dataKey="mae"
          name="MAE"
          stroke="var(--c-forecast)"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
        <Line
          dataKey="bias"
          name="Bias"
          stroke="var(--c-band)"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
        <Line
          dataKey="margin"
          name="P10 safety margin"
          stroke="var(--c-margin)"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
