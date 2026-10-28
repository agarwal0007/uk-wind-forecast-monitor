import type { Metrics } from "../types/api";
import { mw, pct } from "../utils/format";

interface Props {
  metrics: Metrics | null;
  loading: boolean;
}

export function KpiCards({ metrics: m, loading }: Props) {
  const bias = m?.bias ?? null;
  const biasLabel =
    bias === null
      ? ""
      : bias > 0
        ? "Over-forecast"
        : bias < 0
          ? "Under-forecast"
          : "Unbiased";
  const margin = m?.p10 ?? null;
  const noPairs = m !== null && m.paired === 0;

  return (
    <div className={`kpis ${loading ? "is-loading" : ""}`}>
      <Kpi
        label="Mean absolute error"
        value={mw(m?.mae)}
        note={
          noPairs
            ? "No forecast qualifies for this selection"
            : m?.nmaePct != null
              ? `${pct(m.nmaePct)} of mean actual (nMAE)`
              : ""
        }
      />
      <Kpi
        label="Bias (forecast − actual)"
        value={bias === null ? "–" : `${bias > 0 ? "+" : ""}${mw(bias)}`}
        note={
          bias === null
            ? ""
            : bias > 0
              ? "Forecast too high on average → under-buying risk"
              : "Forecast too low on average → over-buying risk"
        }
        tag={biasLabel}
        tone={bias !== null && bias > 0 ? "warn" : "neutral"}
      />
      <Kpi
        label="P10 safety margin"
        value={margin === null ? "–" : mw(Math.max(0, -margin))}
        note={
          margin === null
            ? ""
            : margin < 0
              ? `90% of hours, wind was no more than this below forecast`
              : `Wind was at or above forecast in 90% of hours`
        }
        tone="accent"
        headline
      />
      <Kpi
        label="Forecast coverage"
        value={pct(m?.coveragePct)}
        note={m ? `${m.withForecast} of ${m.targets} hourly targets have a forecast` : ""}
        tone={m?.coveragePct != null && m.coveragePct < 95 ? "warn" : "neutral"}
      />
    </div>
  );
}

interface KpiProps {
  label: string;
  value: string;
  note: string;
  tag?: string;
  tone?: "neutral" | "warn" | "accent";
  headline?: boolean;
}

function Kpi({ label, value, note, tag, tone = "neutral", headline }: KpiProps) {
  return (
    <div className={`kpi tone-${tone} ${headline ? "kpi-headline" : ""}`}>
      <div className="kpi-label">
        {label}
        {tag && <span className={`tag tone-${tone}`}>{tag}</span>}
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-note">{note}</div>
    </div>
  );
}
