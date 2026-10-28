import { useEffect, useState } from "react";

export interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Runs `load` whenever `key` changes, aborting the previous request.
 * Keeps the last good data while a new request is in flight.
 */
export function useFetch<T>(key: string, load: (signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    const ctrl = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    load(ctrl.signal)
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((err: unknown) => {
        if (ctrl.signal.aborted) return;
        const message = err instanceof Error ? err.message : String(err);
        setState({ data: null, loading: false, error: message });
      });
    return () => ctrl.abort();
    // `load` is recreated every render; `key` captures its inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return state;
}
