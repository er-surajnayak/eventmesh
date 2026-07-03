// Internal analytics abstraction — a single seam the app calls, so a real
// provider (GA4/GTM/PostHog/…) can be attached later without touching call
// sites. Deliberately dependency-free and privacy-safe: we emit event names and
// non-PII properties (filter values, event kind/provider, counts) only.

export const EVENTS = {
  PAGE_VIEW: 'page_view',
  SEARCH: 'search',
  FILTER_CHANGE: 'filter_change',
  EVENT_CLICK: 'event_click',
  LOAD_MORE: 'load_more',
  THEME_TOGGLE: 'theme_toggle',
};

const buffer = [];
const listeners = new Set();
const MAX_BUFFER = 200;

export function track(name, props = {}) {
  const event = { name, props, ts: Date.now() };
  buffer.push(event);
  if (buffer.length > MAX_BUFFER) buffer.shift();

  if (typeof window !== 'undefined') {
    // Forward to a GTM-style dataLayer if the host page provides one.
    if (Array.isArray(window.dataLayer)) window.dataLayer.push({ event: name, ...props });
    if (import.meta.env?.DEV) {
      console.debug('[analytics]', name, props);
      (window.__eventmeshAnalytics ||= []).push(event); // dev-only inspection buffer
    }
  }
  for (const fn of listeners) {
    try {
      fn(event);
    } catch {
      /* a bad listener must never break the app */
    }
  }
}

/** Subscribe to tracked events (returns an unsubscribe fn). */
export function onTrack(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** Recent events, for debugging / test assertions. */
export function getEventBuffer() {
  return [...buffer];
}
