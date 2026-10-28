import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle?: string;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  actions?: ReactNode;
  className?: string;
  children: ReactNode;
}

/** Card wrapper that owns the loading / error / empty states for a chart. */
export function Panel({
  title,
  subtitle,
  loading,
  error,
  empty,
  actions,
  className,
  children,
}: Props) {
  let body: ReactNode = children;
  if (error) body = <div className="state state-error">Couldn’t load: {error}</div>;
  else if (empty && !loading)
    body = <div className="state">No data for this selection.</div>;

  return (
    <section className={`panel ${className ?? ""}`} aria-busy={loading}>
      <header className="panel-head">
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
        <div className="panel-actions">
          {loading && <span className="spinner" aria-label="Loading" />}
          {actions}
        </div>
      </header>
      <div className={`panel-body ${loading ? "is-loading" : ""}`}>{body}</div>
    </section>
  );
}
