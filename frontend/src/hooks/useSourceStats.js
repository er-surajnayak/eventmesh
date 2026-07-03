import { useEffect, useState } from 'react';
import { api } from '../lib/apiClient';

// Known providers surfaced in the UI, with their brand dot colors. Counts are
// pulled live so the Hero badge and Sources strip never show fabricated numbers.
const SOURCES = [
  { slug: 'eventmesh', name: 'EventMesh', color: '#00D6FF' },
  { slug: 'eventbrite', name: 'Eventbrite', color: '#FF8A65' },
  { slug: 'meetup', name: 'Meetup', color: '#FF4D4D' },
  { slug: 'luma', name: 'Luma', color: '#C084FC' },
];

// Each event has exactly one provider, so per-source totals sum to the feed
// total. We fetch counts with limit=1 (only `total` is needed) — cheap, and it
// avoids a separate aggregate endpoint for the MVP.
export function useSourceStats() {
  const [stats, setStats] = useState({ sources: [], total: 0, sourceCount: 0, loading: true });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const results = await Promise.all(
          SOURCES.map(async (s) => {
            const data = await api.browseEvents({ source: s.slug, limit: 1 });
            return { ...s, count: data.total ?? 0 };
          }),
        );
        if (cancelled) return;
        const active = results.filter((s) => s.count > 0);
        setStats({
          sources: active,
          total: results.reduce((sum, s) => sum + s.count, 0),
          sourceCount: active.length,
          loading: false,
        });
      } catch {
        if (!cancelled) setStats({ sources: [], total: 0, sourceCount: 0, loading: false });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return stats;
}
