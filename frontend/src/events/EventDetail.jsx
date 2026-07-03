import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { Icon, PlatformBadge, PriceTag } from '../components/UIPrimitives';
import { api } from '../lib/apiClient';
import { priceLabel, hueFromId } from '../utils/adaptEvent';
import { useDocumentHead, buildEventJsonLd, canonicalUrl } from '../lib/seo';
import { track, EVENTS } from '../lib/analytics';

function detailHead(slug, status, event) {
  const canonical = canonicalUrl(`/events/${slug}`);
  if (status === 'ready' && event) {
    const desc = (event.description || `${event.title} — hosted on EventMesh.`).slice(0, 200);
    return {
      title: `${event.title} · EventMesh`,
      description: desc,
      canonical,
      image: event.cover_image_url || undefined,
      type: 'article',
      jsonLd: buildEventJsonLd(event, canonical),
    };
  }
  if (status === 'notfound') return { title: 'Event not found · EventMesh', description: 'This event could not be found.', canonical };
  return { title: 'Event · EventMesh', description: 'An event hosted on EventMesh.', canonical };
}

function formatRange(start, end) {
  if (!start) return 'Date to be announced';
  const s = new Date(start);
  const startStr = s.toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });
  if (!end) return startStr;
  const e = new Date(end);
  const sameDay = s.toDateString() === e.toDateString();
  const endStr = e.toLocaleString('en-US',
    sameDay
      ? { hour: 'numeric', minute: '2-digit' }
      : { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  return `${startStr} – ${endStr}`;
}

// EventMesh destination page for a native (hosted) event. Imported events never
// reach here — they deep-link out to their source from the card.
export function EventDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | ready | notfound | error

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    api.getEvent(slug)
      .then((data) => {
        if (!cancelled) {
          setEvent(data);
          setStatus('ready');
          track(EVENTS.PAGE_VIEW, { path: '/events/:slug', kind: 'native' });
        }
      })
      .catch((err) => { if (!cancelled) setStatus(err.status === 404 ? 'notfound' : 'error'); });
    return () => { cancelled = true; };
  }, [slug]);

  useDocumentHead(detailHead(slug, status, event));

  const isOnline = event?.event_type === 'online';
  const location = isOnline
    ? 'Online / Remote'
    : [event?.venue_name, event?.venue_address, event?.city, event?.country].filter(Boolean).join(' · ') || 'Location to be announced';

  return (
    <>
      <Navbar onExplore={() => navigate('/#discover')} />
      <main style={{ minHeight: '100vh', paddingTop: 64, background: 'var(--bg)' }}>
        <div className="container" style={{ maxWidth: 860, paddingTop: 40, paddingBottom: 80 }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--fg-2)', fontSize: 13.5, marginBottom: 28 }}>
            <span style={{ transform: 'rotate(180deg)' }}>{Icon.arrow}</span> Back to discovery
          </Link>

          {status === 'loading' && (
            <div style={{ color: 'var(--fg-2)', padding: '80px 0', textAlign: 'center' }}>Loading event…</div>
          )}

          {status === 'notfound' && (
            <StateBlock title="Event not found." body="This event may have been unpublished, cancelled, or the link is incorrect.">
              <Link to="/" style={ctaStyle}>Browse events</Link>
            </StateBlock>
          )}

          {status === 'error' && (
            <StateBlock title="Couldn’t load this event." body="Something went wrong reaching the server. The API may be waking from sleep.">
              <button onClick={() => navigate(0)} style={ctaStyle}>Try again</button>
            </StateBlock>
          )}

          {status === 'ready' && event && (
            <article>
              <div style={{
                height: 220, borderRadius: 16, overflow: 'hidden', marginBottom: 28,
                border: '1px solid var(--line)',
                background: event.cover_image_url
                  ? `center/cover no-repeat url(${event.cover_image_url})`
                  : `linear-gradient(135deg, oklch(0.30 0.09 ${hueFromId(event.id)}) 0%, oklch(0.14 0.05 ${hueFromId(event.id)}) 100%)`,
              }} />

              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
                <PlatformBadge platform="EventMesh" />
                <PriceTag price={priceLabel(event.is_free, event.price_cents, event.currency)} />
                <span className="mono" style={{ fontSize: 10.5, color: 'var(--fg-3)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                  Hosted on EventMesh
                </span>
              </div>

              <h1 style={{ margin: 0, fontSize: 'clamp(28px, 4vw, 40px)', letterSpacing: '-0.02em', fontWeight: 600, lineHeight: 1.1 }}>
                {event.title}
              </h1>

              <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 12, color: 'var(--fg-2)', fontSize: 14.5 }}>
                <Row icon={Icon.calendar}>{formatRange(event.start_time, event.end_time)}{event.timezone ? ` · ${event.timezone}` : ''}</Row>
                <Row icon={isOnline ? Icon.clock : Icon.pin}>{location}</Row>
                {event.capacity != null && <Row icon={Icon.users}>Capacity {event.capacity}</Row>}
              </div>

              {event.description && (
                <p style={{ marginTop: 28, fontSize: 15.5, lineHeight: 1.7, color: 'var(--fg)', whiteSpace: 'pre-wrap' }}>
                  {event.description}
                </p>
              )}

              {event.refund_policy && (
                <p style={{ marginTop: 20, fontSize: 13, lineHeight: 1.6, color: 'var(--fg-3)' }}>
                  <strong style={{ color: 'var(--fg-2)' }}>Refund policy:</strong> {event.refund_policy}
                </p>
              )}
            </article>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}

const ctaStyle = {
  display: 'inline-block', padding: '11px 18px', borderRadius: 999,
  background: 'transparent', border: '1px solid var(--line-2)',
  color: 'var(--fg)', fontSize: 13.5, textDecoration: 'none',
};

function Row({ icon, children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ color: 'var(--fg-3)' }}>{icon}</span>
      <span>{children}</span>
    </div>
  );
}

function StateBlock({ title, body, children }) {
  return (
    <div style={{
      border: '1px dashed var(--line-2)', borderRadius: 16,
      padding: '60px 24px', textAlign: 'center', background: 'var(--bg-2)',
    }}>
      <h3 style={{ margin: 0, fontSize: 18, fontWeight: 500 }}>{title}</h3>
      <p style={{ margin: '10px 0 22px', color: 'var(--fg-2)', fontSize: 14 }}>{body}</p>
      {children}
    </div>
  );
}
