import { useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from "recharts";
import type { SeriesPoint } from "../types/api";
import { gw, mw, utcDay, utcLabel } from "../utils/format";

interface Row extends SeriesPoint {
  t: number;
  band: [number, number] | null;
}

export function SeriesChart({ points }: { points: SeriesPoint[] }) {
  const rows = useMemo<Row[]>(
    () =>
      points.map((p) => ({
        ...p,
        t: Date.parse(p.startTime),
        band:
          p.actual !== null && p.forecast !== null
            ? [Math.min(p.actual, p.forecast), Math.max(p.actual, p.forecast)]
            : null,
      })),
    [points],
  );
  const ticks = useMemo(() => dayTicks(rows), [rows]);

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis
          dataKey="t"
          type="number"
          scale="time"
          domain={["dataMin", "dataMax"]}
          ticks={ticks}
          tickFormatter={(t: number) => utcDay(new Date(t).toISOString())}
          stroke="var(--axis)"
          tick={{ fontSize: 12 }}
        />
        <YAxis
          tickFormatter={gw}
          stroke="var(--axis)"
          tick={{ fontSize: 12 }}
          width={56}
        />
        <Tooltip content={<SeriesTooltip />} />
        <Legend wrapperStyle={{ fontSize: 13 }} />
        <Area
          dataKey="band"
          name="Error"
          stroke="none"
          fill="var(--c-band)"
          fillOpacity={0.35}
          isAnimationActive={false}
          connectNulls={false}
          legendType="square"
        />
        <Line
          dataKey="actual"
          name="Actual"
          stroke="var(--c-actual)"
          strokeWidth={1.75}
          dot={false}
          isAnimationActive={false}
          connectNulls={false}
        />
        <Line
          dataKey="forecast"
          name="Forecast"
          stroke="var(--c-forecast)"
          strokeWidth={1.75}
          dot={false}
          isAnimationActive={false}
          connectNulls={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

const DAY_MS = 86_400_000;

/** Midnight ticks, thinned to at most ~10 labels. */
function dayTicks(rows: Row[]): number[] {
  const first = rows[0]?.t;
  const last = rows[rows.length - 1]?.t;
  if (first === undefined || last === undefined) return [];
  const start = Math.ceil(first / DAY_MS) * DAY_MS;
  const step = Math.max(1, Math.ceil((last - start) / DAY_MS / 10)) * DAY_MS;
  const ticks: number[] = [];
  for (let t = start; t <= last; t += step) ticks.push(t);
  return ticks;
}

function SeriesTooltip({ active, payload }: TooltipProps<number, string>) {
  const row = payload?.[0]?.payload as Row | undefined;
  if (!active || !row) return null;
  return (
    <div className="tooltip">
      <div className="tooltip-title">{utcLabel(row.startTime)} UTC</div>
      <dl>
        <dt>
          <i style={{ background: "var(--c-actual)" }} />
          Actual
        </dt>
        <dd>{mw(row.actual)}</dd>
        <dt>
          <i style={{ background: "var(--c-forecast)" }} />
          Forecast
        </dt>
        <dd>{mw(row.forecast)}</dd>
        <dt>Error (f − a)</dt>
        <dd>
          {row.error === null ? "–" : `${row.error > 0 ? "+" : ""}${mw(row.error)}`}
        </dd>
        <dt>Published</dt>
        <dd>{row.publishTime ? `${utcLabel(row.publishTime)}` : "no forecast"}</dd>
        <dt>Horizon</dt>
        <dd>{row.horizonHours === null ? "–" : `${row.horizonHours} h`}</dd>
      </dl>
    </div>
  );
}
