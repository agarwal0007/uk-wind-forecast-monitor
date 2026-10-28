const mwFmt = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

export function mw(v: number | null | undefined): string {
  return v === null || v === undefined ? "–" : `${mwFmt.format(v)} MW`;
}

export function gw(v: number): string {
  return `${(v / 1000).toFixed(1)} GW`;
}

export function pct(v: number | null | undefined, digits = 1): string {
  return v === null || v === undefined ? "–" : `${v.toFixed(digits)}%`;
}

/** "Mon 05 Jan 14:00" in UTC */
export function utcLabel(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

export function utcDay(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    timeZone: "UTC",
  });
}
