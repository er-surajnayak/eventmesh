import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../lib/apiClient';
import { buildBrowseParams } from '../utils/adaptEvent';

const PAGE_SIZE = 12;
const DEBOUNCE_MS = 300;

// Drives the public discovery feed from GET /api/v1/events:
//  - debounces filter changes (so typing in search doesn't fire per keystroke),
//  - aborts the in-flight request when filters change again (no stale overwrites),
//  - exposes offset pagination via loadMore() that appends to the list.
export function useEventFeed(filters) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [nextOffset, setNextOffset] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | ready | error
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  // Serialized so the effect only re-runs on an actual filter change, not on
  // every re-render (the parent recreates the filters object each render).
  const key = JSON.stringify(filters);
  const filtersRef = useRef(filters);
  filtersRef.current = filters;
  const controllerRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(async () => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;

      setStatus('loading');
      setError(null);
      try {
        const params = buildBrowseParams(filtersRef.current, { limit: PAGE_SIZE, offset: 0 });
        const data = await api.browseEvents(params, { signal: controller.signal });
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
        setNextOffset(data.next_offset ?? null);
        setStatus('ready');
      } catch (err) {
        if (cancelled || err.name === 'AbortError') return;
        setError(err);
        setStatus('error');
      }
    }, DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [key]);

  const loadMore = useCallback(async () => {
    if (nextOffset == null || loadingMore) return;
    setLoadingMore(true);
    try {
      const params = buildBrowseParams(filtersRef.current, {
        limit: PAGE_SIZE,
        offset: nextOffset,
      });
      const data = await api.browseEvents(params);
      setItems((prev) => [...prev, ...data.items]);
      setTotal(data.total);
      setNextOffset(data.next_offset ?? null);
    } catch (err) {
      setError(err);
    } finally {
      setLoadingMore(false);
    }
  }, [nextOffset, loadingMore]);

  const reload = useCallback(() => {
    // Manual page-0 refetch for the error-state "Try again" button (the effect
    // key is unchanged, so we can't rely on it re-firing).
    (async () => {
      setStatus('loading');
      setError(null);
      try {
        const params = buildBrowseParams(filtersRef.current, { limit: PAGE_SIZE, offset: 0 });
        const data = await api.browseEvents(params);
        setItems(data.items);
        setTotal(data.total);
        setNextOffset(data.next_offset ?? null);
        setStatus('ready');
      } catch (err) {
        setError(err);
        setStatus('error');
      }
    })();
  }, []);

  return {
    items,
    total,
    status,
    error,
    loadingMore,
    hasMore: nextOffset != null,
    loadMore,
    reload,
  };
}
