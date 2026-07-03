import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/apiClient';
import { formatEventDate } from '../utils/formatDate';
import { useOrganizer } from './OrganizerContext';
import { Button, StatusBadge } from './components/fields';

const DRAFT_STATES = ['draft', 'preview', 'pending_review'];

export function EventPreview() {
  const { currentSlug } = useOrganizer();
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!currentSlug) return;
    try {
      setEvent(await api.getOrgEvent(currentSlug, eventId));
    } catch (err) {
      setError(err.message);
    }
  }, [currentSlug, eventId]);

  useEffect(() => { load(); }, [load]);

  const act = async (action) => {
    setBusy(true);
    setError('');
    try {
      await api.eventAction(currentSlug, eventId, action);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (error && !event) return <p style={{ color: '#ff6b6b' }}>{error}</p>;
  if (!event) return <p style={{ color: 'var(--fg-2)' }}>Loading…</p>;

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <button onClick={() => navigate('/organizer')} style={{ background: 'none', border: 'none', color: 'var(--fg-2)', fontSize: 13, cursor: 'pointer' }}>
          ← Dashboard
        </button>
        <StatusBadge status={event.status} />
      </div>

      {/* Preview card */}
      <div style={{ background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 16, overflow: 'hidden' }}>
        <div style={{ height: 120, background: `linear-gradient(135deg, oklch(0.26 0.07 210) 0%, oklch(0.14 0.05 210) 100%)`, borderBottom: '1px solid var(--line)' }} />
        <div style={{ padding: 24 }}>
          <div className="mono" style={{ fontSize: 10.5, color: 'var(--fg-3)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
            {event.event_type} · {event.visibility}
          </div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600, letterSpacing: '-0.02em' }}>{event.title}</h1>
          {event.description && <p style={{ color: 'var(--fg-2)', fontSize: 14, lineHeight: 1.6, marginTop: 12 }}>{event.description}</p>}
          <div style={{ marginTop: 18, paddingTop: 16, borderTop: '1px solid var(--line)', display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: 'var(--fg-2)' }}>
            <span>📅 {event.start_time ? formatEventDate(event.start_time) : 'No date set'}</span>
            <span>📍 {event.venue_name || (event.event_type === 'online' ? 'Online' : event.city || 'Location TBD')}</span>
            <span>🎟 {event.is_free ? 'Free' : `${event.price_cents ?? 0} ${event.currency || ''}`}{event.capacity ? ` · ${event.capacity} spots` : ''}</span>
          </div>
        </div>
      </div>

      {error && <p style={{ color: '#ff6b6b', fontSize: 12.5, marginTop: 12 }}>{error}</p>}

      {/* Publish flow / lifecycle actions */}
      <div style={{ display: 'flex', gap: 10, marginTop: 20, flexWrap: 'wrap' }}>
        <Button variant="ghost" onClick={() => navigate(`/organizer/events/${event.id}/edit`)}>Edit</Button>
        {DRAFT_STATES.includes(event.status) && (
          <Button disabled={busy || !event.start_time} onClick={() => act('submit')}>
            {busy ? 'Working…' : 'Publish'}
          </Button>
        )}
        {event.status === 'published' && (
          <Button variant="ghost" disabled={busy} onClick={() => act('hide')}>Hide</Button>
        )}
        {event.status === 'hidden' && (
          <Button disabled={busy} onClick={() => act('unhide')}>Unhide</Button>
        )}
        {!['cancelled', 'archived'].includes(event.status) && (
          <Button variant="danger" disabled={busy} onClick={() => act('cancel')}>Cancel</Button>
        )}
        {event.status !== 'archived' && (
          <Button variant="ghost" disabled={busy} onClick={() => act('archive')}>Archive</Button>
        )}
      </div>
      {DRAFT_STATES.includes(event.status) && !event.start_time && (
        <p style={{ color: '#ffb84d', fontSize: 12.5, marginTop: 10 }}>Add a start time before publishing.</p>
      )}
    </div>
  );
}
