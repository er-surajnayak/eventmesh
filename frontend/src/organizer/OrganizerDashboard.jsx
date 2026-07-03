import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/apiClient';
import { formatEventDate } from '../utils/formatDate';
import { useOrganizer } from './OrganizerContext';
import { Button, Segmented, StatusBadge, TextInput } from './components/fields';

const TABS = [
  { key: 'drafts', label: 'Drafts', statuses: ['draft', 'preview', 'pending_review'] },
  { key: 'published', label: 'Published', statuses: ['published', 'hidden'] },
  { key: 'archived', label: 'Archived', statuses: ['cancelled', 'archived'] },
];

function StatCard({ label, value, soon }) {
  return (
    <div
      style={{
        flex: '1 1 160px', background: 'var(--bg-2)', border: '1px solid var(--line)',
        borderRadius: 14, padding: '18px 20px',
      }}
    >
      <div className="mono" style={{ fontSize: 10.5, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--fg-3)' }}>
        {label}
      </div>
      <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 26, fontWeight: 600 }}>{value}</span>
        {soon && (
          <span className="mono" style={{ fontSize: 9, color: 'var(--accent)', border: '1px solid rgba(0,214,255,0.3)', borderRadius: 5, padding: '2px 6px' }}>
            SOON
          </span>
        )}
      </div>
    </div>
  );
}

function CreateFirstOrg() {
  const { reloadOrgs, setCurrentSlug } = useOrganizer();
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const create = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const org = await api.createOrganization({ name: name.trim() });
      await reloadOrgs();
      setCurrentSlug(org.slug);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 420, margin: '48px auto', textAlign: 'center' }}>
      <h2 style={{ fontWeight: 600, marginBottom: 8 }}>Create your organization</h2>
      <p style={{ color: 'var(--fg-2)', fontSize: 14, marginBottom: 20 }}>
        Events are hosted under an organization. Name yours to get started.
      </p>
      <form onSubmit={create} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <TextInput value={name} onChange={setName} placeholder="Organization name" required />
        <Button type="submit" disabled={busy}>{busy ? 'Creating…' : 'Create organization'}</Button>
      </form>
      {error && <p style={{ color: '#ff6b6b', fontSize: 12.5, marginTop: 10 }}>{error}</p>}
    </div>
  );
}

function EventRow({ event, orgSlug, onChanged }) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);

  const act = async (action) => {
    setBusy(true);
    try {
      await api.eventAction(orgSlug, event.id, action);
      await onChanged();
    } catch (err) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="org-event-row"
      style={{
        display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
        border: '1px solid var(--line)', borderRadius: 12, background: 'var(--bg-2)',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 15, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {event.title}
        </div>
        <div style={{ fontSize: 12, color: 'var(--fg-3)', marginTop: 4 }}>
          {event.start_time ? formatEventDate(event.start_time) : 'No date yet'} · {event.event_type}
        </div>
      </div>
      <StatusBadge status={event.status} />
      <div className="org-row-actions" style={{ display: 'flex', gap: 8 }}>
        <Button variant="ghost" style={{ padding: '7px 12px', fontSize: 12.5 }} onClick={() => navigate(`/organizer/events/${event.id}/edit`)}>
          Edit
        </Button>
        <Button variant="ghost" style={{ padding: '7px 12px', fontSize: 12.5 }} onClick={() => navigate(`/organizer/events/${event.id}/preview`)}>
          Preview
        </Button>
        {event.status === 'published' && (
          <Button variant="ghost" disabled={busy} style={{ padding: '7px 12px', fontSize: 12.5 }} onClick={() => act('hide')}>
            Hide
          </Button>
        )}
        {event.status === 'hidden' && (
          <Button disabled={busy} style={{ padding: '7px 12px', fontSize: 12.5 }} onClick={() => act('unhide')}>
            Unhide
          </Button>
        )}
      </div>
    </div>
  );
}

export function OrganizerDashboard() {
  const { currentOrg, currentSlug } = useOrganizer();
  const navigate = useNavigate();
  const [events, setEvents] = useState(null);
  const [tab, setTab] = useState('drafts');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!currentSlug) return;
    setError('');
    try {
      setEvents(await api.listOrgEvents(currentSlug));
    } catch (err) {
      setError(err.message);
    }
  }, [currentSlug]);

  useEffect(() => { load(); }, [load]);

  if (!currentOrg) return <CreateFirstOrg />;

  const activeStatuses = TABS.find((t) => t.key === tab).statuses;
  const filtered = (events || []).filter((e) => activeStatuses.includes(e.status));
  const publishedCount = (events || []).filter((e) => e.status === 'published').length;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 16, marginBottom: 22, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 600, letterSpacing: '-0.02em' }}>Dashboard</h1>
          <div style={{ fontSize: 13, color: 'var(--fg-3)', marginTop: 4 }}>{currentOrg.name}</div>
        </div>
        <Button onClick={() => navigate('/organizer/events/new')}>+ New event</Button>
      </div>

      {/* Analytics — UI exposed, values are placeholders for now. */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 26 }}>
        <StatCard label="Events" value={events ? events.length : '—'} />
        <StatCard label="Published" value={events ? publishedCount : '—'} />
        <StatCard label="Registrations" value="—" soon />
        <StatCard label="Page views" value="—" soon />
      </div>

      <div style={{ marginBottom: 18 }}>
        <Segmented value={tab} onChange={setTab} options={TABS.map((t) => ({ value: t.key, label: t.label }))} />
      </div>

      {error && <p style={{ color: '#ff6b6b', fontSize: 13 }}>{error}</p>}
      {!events && <p style={{ color: 'var(--fg-2)', fontSize: 13 }}>Loading events…</p>}
      {events && filtered.length === 0 && (
        <div style={{ border: '1px dashed var(--line-2)', borderRadius: 14, padding: '48px 24px', textAlign: 'center', color: 'var(--fg-2)' }}>
          <p style={{ margin: 0, fontSize: 14 }}>No {tab} events yet.</p>
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.map((e) => (
          <EventRow key={e.id} event={e} orgSlug={currentSlug} onChanged={load} />
        ))}
      </div>
    </div>
  );
}
