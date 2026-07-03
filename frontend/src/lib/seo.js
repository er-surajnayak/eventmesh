import { useEffect } from 'react';

// Dependency-free document-head management for the SPA. JS-executing crawlers
// (Google, etc.) read what we set here; static defaults in index.html cover the
// rest. We upsert tags in place rather than add/remove, since only one route is
// mounted at a time.

const SITE_NAME = 'EventMesh';

function upsertMeta(attr, key, content) {
  if (content == null || content === '') return;
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute('content', String(content));
}

function upsertLink(rel, href) {
  if (!href) return;
  let el = document.head.querySelector(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement('link');
    el.setAttribute('rel', rel);
    document.head.appendChild(el);
  }
  el.setAttribute('href', href);
}

function setJsonLd(obj) {
  const id = 'ld-json-dynamic';
  let el = document.getElementById(id);
  if (!obj) {
    if (el) el.remove();
    return;
  }
  if (!el) {
    el = document.createElement('script');
    el.type = 'application/ld+json';
    el.id = id;
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(obj);
}

export function useDocumentHead({ title, description, canonical, image, type = 'website', jsonLd }) {
  // Serialize jsonLd for the dependency array so identical objects don't re-run.
  const jsonLdKey = jsonLd ? JSON.stringify(jsonLd) : '';
  useEffect(() => {
    if (title) document.title = title;
    upsertMeta('name', 'description', description);

    upsertMeta('property', 'og:site_name', SITE_NAME);
    upsertMeta('property', 'og:title', title);
    upsertMeta('property', 'og:description', description);
    upsertMeta('property', 'og:type', type);
    if (canonical) {
      upsertMeta('property', 'og:url', canonical);
      upsertLink('canonical', canonical);
    }
    upsertMeta('name', 'twitter:card', image ? 'summary_large_image' : 'summary');
    upsertMeta('name', 'twitter:title', title);
    upsertMeta('name', 'twitter:description', description);
    if (image) {
      upsertMeta('property', 'og:image', image);
      upsertMeta('name', 'twitter:image', image);
    }

    setJsonLd(jsonLd);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title, description, canonical, image, type, jsonLdKey]);
}

/** Absolute canonical URL for the current origin + path. */
export function canonicalUrl(path = '/') {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://eventmesh.xyz';
  return `${origin}${path}`;
}

function offersFor(isFree, priceCents, currency, url) {
  if (isFree) {
    return { '@type': 'Offer', price: 0, priceCurrency: (currency || 'USD').toUpperCase(), availability: 'https://schema.org/InStock', url };
  }
  if (priceCents == null) return undefined;
  return {
    '@type': 'Offer',
    price: (priceCents / 100).toFixed(2),
    priceCurrency: (currency || 'USD').toUpperCase(),
    availability: 'https://schema.org/InStock',
    url,
  };
}

/** schema.org Event from a native EventRead payload. */
export function buildEventJsonLd(event, canonical) {
  const isOnline = event.event_type === 'online';
  const location = isOnline
    ? { '@type': 'VirtualLocation', url: canonical }
    : {
        '@type': 'Place',
        name: event.venue_name || event.city || 'Venue TBA',
        address: [event.venue_address, event.city, event.country].filter(Boolean).join(', ') || undefined,
      };
  return {
    '@context': 'https://schema.org',
    '@type': 'Event',
    name: event.title,
    startDate: event.start_time || undefined,
    endDate: event.end_time || undefined,
    eventAttendanceMode: isOnline
      ? 'https://schema.org/OnlineEventAttendanceMode'
      : 'https://schema.org/OfflineEventAttendanceMode',
    eventStatus: 'https://schema.org/EventScheduled',
    location,
    image: event.cover_image_url || undefined,
    description: event.description || undefined,
    offers: offersFor(event.is_free, event.price_cents, event.currency, canonical),
    organizer: { '@type': 'Organization', name: SITE_NAME },
  };
}

/** schema.org ItemList of visible events (raw API items) for the discovery page. */
export function buildEventListJsonLd(items, origin) {
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    itemListElement: items.slice(0, 20).map((e, i) => {
      const url = e.kind === 'native' && e.slug ? `${origin}/events/${e.slug}` : e.url;
      return {
        '@type': 'ListItem',
        position: i + 1,
        item: {
          '@type': 'Event',
          name: e.title,
          startDate: e.start_time || undefined,
          url: url || undefined,
          image: e.image_url || undefined,
          location: e.is_online
            ? { '@type': 'VirtualLocation', url: url || undefined }
            : { '@type': 'Place', name: e.venue || e.city || 'Venue TBA' },
        },
      };
    }),
  };
}
