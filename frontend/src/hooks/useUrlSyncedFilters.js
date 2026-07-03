import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

// Mirrors the discovery filters to the URL query string so a search is
// shareable/bookmarkable and browser back/forward navigates filter history.
// Only non-default values are written, keeping URLs clean (/, /?q=jazz&city=Berlin).
const KEYS = ['q', 'city', 'source', 'date', 'price', 'type'];

export function useUrlSyncedFilters(defaults) {
  const [params, setParams] = useSearchParams();

  const filters = useMemo(() => {
    const f = { ...defaults };
    for (const k of KEYS) {
      const v = params.get(k);
      if (v != null) f[k] = v;
    }
    return f;
  }, [params, defaults]);

  const setFilters = useCallback(
    (updater) => {
      setParams(
        (prev) => {
          const current = { ...defaults };
          for (const k of KEYS) {
            const v = prev.get(k);
            if (v != null) current[k] = v;
          }
          const next = typeof updater === 'function' ? updater(current) : updater;
          const sp = new URLSearchParams();
          for (const k of KEYS) {
            if (next[k] != null && next[k] !== defaults[k]) sp.set(k, next[k]);
          }
          return sp;
        },
        { replace: true },
      );
    },
    [setParams, defaults],
  );

  return [filters, setFilters];
}
