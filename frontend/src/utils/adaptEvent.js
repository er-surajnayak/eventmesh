// Adapts the canonical API event model (VisibleEventRead from GET /api/v1/events)
// onto the shape the existing EventCard/design expects — no UI redesign, just a
// translation layer. Keeping this isolated means the card components never learn
// the API's field names, and the backend contract can evolve behind it.

import { cityQueryValue } from '../data/cities';

const PROVIDER_LABELS = {
  eventmesh: 'EventMesh',
  eventbrite: 'Eventbrite',
  meetup: 'Meetup',
  luma: 'Luma',
  ticketmaster: 'Ticketmaster',
};

// UI-facing source options (label shown in the filter; slug sent to the API).
export const SOURCE_OPTIONS = ['All sources', 'EventMesh', 'Eventbrite', 'Meetup', 'Luma'];

const SOURCE_LABEL_TO_SLUG = {
  EventMesh: 'eventmesh',
  Eventbrite: 'eventbrite',
  Meetup: 'meetup',
  Luma: 'luma',
};

const CURRENCY_SYMBOLS = { USD: '$', CAD: '$', AUD: '$', EUR: '€', GBP: '£', INR: '₹' };

export function providerLabel(provider) {
  if (!provider) return 'Event';
  return PROVIDER_LABELS[provider] || provider.charAt(0).toUpperCase() + provider.slice(1);
}

/** Human price string for the PriceTag: 'Free', '$18', '₹500', or 'Paid'. */
export function priceLabel(isFree, priceCents, currency) {
  if (isFree) return 'Free';
  if (priceCents == null) return 'Paid';
  const code = currency?.toUpperCase();
  const symbol = CURRENCY_SYMBOLS[code] || (code ? `${code} ` : '');
  const amount = priceCents / 100;
  const formatted = Number.isInteger(amount) ? String(amount) : amount.toFixed(2);
  return `${symbol}${formatted}`;
}

/** Deterministic hue (0–359) from an id so cards keep stable, varied gradients. */
export function hueFromId(id) {
  let hash = 0;
  const str = String(id);
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) & 0xffffffff;
  }
  return Math.abs(hash) % 360;
}

/** Other providers in the canonical group, for natural provenance display. */
function otherSources(provider, sources) {
  if (!Array.isArray(sources)) return [];
  return sources.filter((s) => s && s !== provider).map(providerLabel);
}

/** Canonical API event → EventCard shape. */
export function toCardEvent(e) {
  const isNative = e.kind === 'native';
  return {
    key: `${e.kind}:${e.id}`,
    id: e.id,
    kind: e.kind,
    title: e.title,
    blurb: e.description || '',
    date: e.start_time,
    is_online: e.is_online,
    venue: e.venue || e.city || null,
    category: e.category || null, // hidden by the card when absent
    platform: providerLabel(e.provider),
    price: priceLabel(e.is_free, e.price_cents, e.currency),
    hue: hueFromId(e.id),
    attendees: null, // not exposed by the API → the card hides the counter
    href: isNative ? (e.slug ? `/events/${e.slug}` : null) : e.url || null,
    external: !isNative,
    alsoOn: otherSources(e.provider, e.sources),
  };
}

/** UI filter state → GET /api/v1/events query params. */
export function buildBrowseParams(filters, { limit, offset } = {}) {
  const params = { limit, offset };
  const q = filters.q?.trim();
  if (q) params.q = q;
  if (filters.city && filters.city !== 'All Cities') params.city = cityQueryValue(filters.city);
  if (filters.date && filters.date !== 'all') params.date_range = filters.date;
  if (filters.price === 'free') params.free = true;
  else if (filters.price === 'paid') params.free = false;
  if (filters.type === 'online') params.online = true;
  else if (filters.type === 'in-person') params.online = false;
  const sourceSlug = SOURCE_LABEL_TO_SLUG[filters.source];
  if (sourceSlug) params.source = sourceSlug;
  return params;
}
