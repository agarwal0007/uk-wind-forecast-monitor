import { useEffect, useState } from "react";
import { api } from "./api/client";
import { Controls } from "./components/Controls";
import { ErrorHistogram } from "./components/ErrorHistogram";
import { HorizonChart } from "./components/HorizonChart";
import { HourChart } from "./components/HourChart";
import { KpiCards } from "./components/KpiCards";
import { Panel } from "./components/Panel";
import { SeriesChart } from "./components/SeriesChart";
import { useDebounced } from "./hooks/useDebounced";
import { useFetch } from "./hooks/useFetch";
import type { Query } from "./types/api";
import { parseQuery, serializeQuery } from "./utils/query";
import { toCsv } from "./utils/stats";

function downloadCsv(name: string, csv: string) {
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [query, setQuery] = useState<Query>(() => parseQuery(window.location.search));
  const q = useDebounced(query, 300);
  useEffect(() => {
    // Keep the URL shareable: it always reflects the current selection.
    window.history.replaceState(null, "", serializeQuery(q));
  }, [q]);
  const key = JSON.stringify(q);
  const rangeKey = `${q.startDate}/${q.endDate}`;

  const series = useFetch(key, (s) => api.series(q, s));
  const metrics = useFetch(key, (s) => api.metrics(q, s));
  const byHour = useFetch(key, (s) => api.byHour(q, s));
  const byHorizon = useFetch(rangeKey, (s) => api.byHorizon(q, s));

  const selLabel =
    q.mode === "horizon"
      ? `latest forecast published ≥ ${q.horizon} h before delivery`
      : `latest forecast published before ${q.cutoff} UTC on D-1`;
  const hasPairs = (metrics.data?.paired ?? 0) > 0;

  return (
    <div className="app">
      <header className="app-head">
        <div className="brand">
          <img src="/favicon.svg" alt="" width={32} height={32} />
          <div>
            <h1>Wind Forecast Monitor</h1>
            <p className="muted">
              GB national wind: the forecast you could have traded on vs what was
              generated. Elexon WINDFOR vs FUELHH, January 2026, all times UTC.
            </p>
          </div>
        </div>
      </header>

      <Controls query={query} onChange={setQuery} />

      {metrics.error && (
        <div className="banner" role="alert">
          Couldn’t load metrics: {metrics.error}
        </div>
      )}

      <KpiCards metrics={metrics.data} loading={metrics.loading} />

      <Panel
        title="Actual vs forecast"
        subtitle={`Hourly, ${selLabel}. Shaded area = error. Gaps = no qualifying forecast.`}
        loading={series.loading}
        error={series.error}
        empty={series.data?.length === 0}
        actions={
          <button
            type="button"
            className="btn"
            disabled={!series.data?.length}
            onClick={() =>
              series.data &&
              downloadCsv(
                `wind-series-${q.startDate}_${q.endDate}.csv`,
                toCsv(series.data),
              )
            }
          >
            Export CSV
          </button>
        }
      >
        <SeriesChart points={series.data ?? []} />
      </Panel>

      <div className="grid">
        <Panel
          title="Error vs horizon"
          subtitle="MAE, bias and P10 margin by forecast lead time. Coverage falls past ~43 h."
          loading={byHorizon.loading}
          error={byHorizon.error}
          empty={byHorizon.data?.every((r) => r.paired === 0)}
        >
          <HorizonChart
            rows={byHorizon.data ?? []}
            current={q.mode === "horizon" ? q.horizon : null}
          />
        </Panel>
        <Panel
          title="Error distribution"
          subtitle="actual − forecast, 500 MW bins. Left of zero = wind came in short."
          loading={series.loading}
          error={series.error}
          empty={!hasPairs}
        >
          <ErrorHistogram points={series.data ?? []} p10={metrics.data?.p10 ?? null} />
        </Panel>
        <Panel
          title="MAE by hour of day"
          subtitle="UTC (= UK time in January)."
          loading={byHour.loading}
          error={byHour.error}
          empty={byHour.data?.every((r) => r.n === 0)}
        >
          <HourChart rows={byHour.data ?? []} />
        </Panel>
      </div>

      <footer className="app-foot muted">
        Data: Elexon Insights API (BMRS) — WINDFOR forecasts, FUELHH WIND outturn. Only
        forecasts with a 0–48 h horizon are considered. Contains BSC Information licensed
        under the BSC Open Data Licence.
      </footer>
    </div>
  );
}
