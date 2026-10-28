import type { Mode, Query } from "../types/api";
import { DATA_END, DATA_START } from "../utils/query";

interface Props {
  query: Query;
  onChange: (q: Query) => void;
}

export function Controls({ query, onChange }: Props) {
  const set = <K extends keyof Query>(k: K, v: Query[K]) =>
    onChange({ ...query, [k]: v });

  return (
    <div className="controls" role="group" aria-label="Selection">
      <label className="field">
        <span>From</span>
        <input
          type="date"
          min={DATA_START}
          max={query.endDate}
          value={query.startDate}
          onChange={(e) => e.target.value && set("startDate", e.target.value)}
        />
      </label>
      <label className="field">
        <span>To</span>
        <input
          type="date"
          min={query.startDate}
          max={DATA_END}
          value={query.endDate}
          onChange={(e) => e.target.value && set("endDate", e.target.value)}
        />
      </label>

      <div className="field">
        <span>Forecast selection</span>
        <div className="segmented" role="radiogroup">
          {(
            [
              ["horizon", "Fixed horizon"],
              ["decision", "D-1 decision time"],
            ] as [Mode, string][]
          ).map(([m, label]) => (
            <button
              key={m}
              type="button"
              role="radio"
              aria-checked={query.mode === m}
              className={query.mode === m ? "active" : ""}
              onClick={() => set("mode", m)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {query.mode === "horizon" ? (
        <label className="field field-grow">
          <span>
            Horizon: <strong>{query.horizon} h</strong> before delivery
          </span>
          <input
            type="range"
            min={0}
            max={48}
            step={1}
            value={query.horizon}
            onChange={(e) => set("horizon", Number(e.target.value))}
          />
        </label>
      ) : (
        <label className="field">
          <span>Cut-off on D-1 (UTC = UK time in January)</span>
          <input
            type="time"
            step={1800}
            value={query.cutoff}
            onChange={(e) => e.target.value && set("cutoff", e.target.value)}
          />
        </label>
      )}
    </div>
  );
}
