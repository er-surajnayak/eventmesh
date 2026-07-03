import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/apiClient';
import { useOrganizer } from './OrganizerContext';
import {
  Button, DateTimeInput, Field, NumberInput, Segmented, TextArea, TextInput, Toggle,
} from './components/fields';

const STEPS = ['Basics', 'Schedule', 'Location', 'Ticketing', 'Review'];

const EMPTY = {
  title: '', description: '', event_type: 'offline', visibility: 'public',
  start_time: '', end_time: '', timezone: '',
  venue_name: '', venue_address: '', city: '', country: '',
  is_free: true, price_cents: null, currency: '', capacity: null,
  registration_required: true, registration_closes_at: '',
  cover_image_url: '', refund_policy: '',
};

function isoToLocal(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
function localToIso(local) {
  return local ? new Date(local).toISOString() : null;
}

function toForm(event) {
  return {
    ...EMPTY,
    ...event,
    start_time: isoToLocal(event.start_time),
    end_time: isoToLocal(event.end_time),
    registration_closes_at: isoToLocal(event.registration_closes_at),
    description: event.description ?? '',
    timezone: event.timezone ?? '',
    venue_name: event.venue_name ?? '',
    venue_address: event.venue_address ?? '',
    city: event.city ?? '',
    country: event.country ?? '',
    currency: event.currency ?? '',
    cover_image_url: event.cover_image_url ?? '',
    refund_policy: event.refund_policy ?? '',
  };
}

function buildPayload(form) {
  const p = {
    title: form.title,
    description: form.description || null,
    event_type: form.event_type,
    visibility: form.visibility,
    start_time: localToIso(form.start_time),
    end_time: localToIso(form.end_time),
    timezone: form.timezone || null,
    venue_name: form.venue_name || null,
    venue_address: form.venue_address || null,
    city: form.city || null,
    country: form.country || null,
    is_free: form.is_free,
    price_cents: form.is_free ? null : form.price_cents,
    currency: form.is_free ? null : form.currency || null,
    capacity: form.capacity,
    registration_required: form.registration_required,
    registration_closes_at: localToIso(form.registration_closes_at),
    cover_image_url: form.cover_image_url || null,
    refund_policy: form.refund_policy || null,
  };
  return p;
}

export function EventWizard({ mode }) {
  const { currentSlug } = useOrganizer();
  const navigate = useNavigate();
  const params = useParams();

  const [form, setForm] = useState(EMPTY);
  const [eventId, setEventId] = useState(mode === 'edit' ? params.eventId : null);
  const [step, setStep] = useState(0);
  const [saveState, setSaveState] = useState('idle'); // idle | saving | saved | error
  const [loaded, setLoaded] = useState(mode === 'create');
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState('');
  const dirty = useRef(false);

  const set = (key, value) => { dirty.current = true; setForm((f) => ({ ...f, [key]: value })); };

  // Load existing event in edit mode.
  useEffect(() => {
    if (mode === 'edit' && currentSlug && params.eventId) {
      api.getOrgEvent(currentSlug, params.eventId)
        .then((e) => { setForm(toForm(e)); setEventId(e.id); setLoaded(true); })
        .catch((err) => { setError(err.message); setLoaded(true); });
    }
  }, [mode, currentSlug, params.eventId]);

  const save = useCallback(async () => {
    if (!currentSlug || form.title.trim().length < 2) return;
    setSaveState('saving');
    try {
      const payload = buildPayload(form);
      if (!eventId) {
        const created = await api.createEvent(currentSlug, payload);
        setEventId(created.id);
        window.history.replaceState(null, '', `/organizer/events/${created.id}/edit`);
      } else {
        await api.updateEvent(currentSlug, eventId, payload);
      }
      dirty.current = false;
      setSaveState('saved');
    } catch (err) {
      setSaveState('error');
      setError(err.message);
    }
  }, [currentSlug, eventId, form]);

  // Debounced autosave.
  useEffect(() => {
    if (!loaded || !dirty.current) return;
    const t = setTimeout(save, 900);
    return () => clearTimeout(t);
  }, [form, loaded, save]);

  const publish = async () => {
    setPublishing(true);
    setError('');
    try {
      if (dirty.current) await save();
      await api.eventAction(currentSlug, eventId, 'submit');
      navigate('/organizer');
    } catch (err) {
      setError(err.message);
    } finally {
      setPublishing(false);
    }
  };

  if (!loaded) return <p style={{ color: 'var(--fg-2)' }}>Loading…</p>;

  const saveLabel = { idle: '', saving: 'Saving…', saved: 'Saved', error: 'Not saved' }[saveState];

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <button onClick={() => navigate('/organizer')} style={{ background: 'none', border: 'none', color: 'var(--fg-2)', fontSize: 13, cursor: 'pointer' }}>
          ← Dashboard
        </button>
        <span className="mono" style={{ fontSize: 11, color: saveState === 'error' ? '#ff6b6b' : 'var(--fg-3)' }}>{saveLabel}</span>
      </div>
      <h1 style={{ margin: '0 0 20px', fontSize: 24, fontWeight: 600 }}>
        {mode === 'create' ? 'Create event' : 'Edit event'}
      </h1>

      {/* Stepper */}
      <div className="wizard-steps" style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {STEPS.map((label, i) => (
          <button
            key={label}
            onClick={() => setStep(i)}
            className="mono"
            style={{
              flex: '1 1 auto', padding: '8px 10px', borderRadius: 8, fontSize: 10.5, letterSpacing: '0.06em',
              textTransform: 'uppercase', cursor: 'pointer', border: '1px solid var(--line)',
              background: i === step ? 'rgba(0,214,255,0.1)' : 'var(--bg-2)',
              color: i === step ? 'var(--accent)' : 'var(--fg-3)',
            }}
          >
            {i + 1}. {label}
          </button>
        ))}
      </div>

      <div style={{ background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 16, padding: 24 }}>
        {step === 0 && (
          <>
            <Field label="Title"><TextInput value={form.title} onChange={(v) => set('title', v)} placeholder="Event title" /></Field>
            <Field label="Description"><TextArea value={form.description} onChange={(v) => set('description', v)} placeholder="What's it about?" /></Field>
            <Field label="Type">
              <Segmented value={form.event_type} onChange={(v) => set('event_type', v)}
                options={[{ value: 'offline', label: 'In-person' }, { value: 'online', label: 'Online' }, { value: 'hybrid', label: 'Hybrid' }]} />
            </Field>
            <Field label="Visibility" hint="Public is listed; unlisted is link-only; private is hidden.">
              <Segmented value={form.visibility} onChange={(v) => set('visibility', v)}
                options={[{ value: 'public', label: 'Public' }, { value: 'unlisted', label: 'Unlisted' }, { value: 'private', label: 'Private' }]} />
            </Field>
          </>
        )}

        {step === 1 && (
          <>
            <Field label="Starts"><DateTimeInput value={form.start_time} onChange={(v) => set('start_time', v)} /></Field>
            <Field label="Ends"><DateTimeInput value={form.end_time} onChange={(v) => set('end_time', v)} /></Field>
            <Field label="Timezone" hint="e.g., Europe/Berlin"><TextInput value={form.timezone} onChange={(v) => set('timezone', v)} placeholder="Timezone" /></Field>
          </>
        )}

        {step === 2 && (
          <>
            <Field label="Venue name"><TextInput value={form.venue_name} onChange={(v) => set('venue_name', v)} /></Field>
            <Field label="Address"><TextInput value={form.venue_address} onChange={(v) => set('venue_address', v)} /></Field>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}><Field label="City"><TextInput value={form.city} onChange={(v) => set('city', v)} /></Field></div>
              <div style={{ flex: 1 }}><Field label="Country"><TextInput value={form.country} onChange={(v) => set('country', v)} /></Field></div>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <Field><Toggle checked={form.is_free} onChange={(v) => set('is_free', v)} label="Free event" /></Field>
            {!form.is_free && (
              <div style={{ display: 'flex', gap: 12 }}>
                <div style={{ flex: 2 }}><Field label="Price (cents)" hint="1500 = 15.00"><NumberInput value={form.price_cents} onChange={(v) => set('price_cents', v)} min={0} /></Field></div>
                <div style={{ flex: 1 }}><Field label="Currency"><TextInput value={form.currency} onChange={(v) => set('currency', v.toUpperCase().slice(0, 3))} placeholder="USD" /></Field></div>
              </div>
            )}
            <Field><Toggle checked={form.registration_required} onChange={(v) => set('registration_required', v)} label="Require registration" /></Field>
            <Field label="Capacity" hint="Leave empty for unlimited"><NumberInput value={form.capacity} onChange={(v) => set('capacity', v)} min={1} /></Field>
            <Field label="Registration closes"><DateTimeInput value={form.registration_closes_at} onChange={(v) => set('registration_closes_at', v)} /></Field>
            <Field label="Refund policy"><TextArea value={form.refund_policy} onChange={(v) => set('refund_policy', v)} rows={3} /></Field>
          </>
        )}

        {step === 4 && (
          <div>
            <h3 style={{ marginTop: 0, fontSize: 16 }}>{form.title || 'Untitled event'}</h3>
            <p style={{ color: 'var(--fg-2)', fontSize: 13.5, whiteSpace: 'pre-wrap' }}>{form.description || 'No description.'}</p>
            <div style={{ fontSize: 12.5, color: 'var(--fg-3)', display: 'flex', flexDirection: 'column', gap: 4, marginTop: 12 }}>
              <span>Type: {form.event_type} · Visibility: {form.visibility}</span>
              <span>Starts: {form.start_time || '—'}</span>
              <span>{form.is_free ? 'Free' : `Paid (${form.price_cents ?? 0} ${form.currency || ''})`}{form.capacity ? ` · Capacity ${form.capacity}` : ''}</span>
            </div>
            {!form.start_time && <p style={{ color: '#ffb84d', fontSize: 12.5, marginTop: 12 }}>Add a start time (step 2) before publishing.</p>}
            <div style={{ marginTop: 20 }}>
              <Button onClick={publish} disabled={publishing || !eventId || !form.start_time}>
                {publishing ? 'Publishing…' : 'Publish event'}
              </Button>
            </div>
          </div>
        )}
      </div>

      {error && <p style={{ color: '#ff6b6b', fontSize: 12.5, marginTop: 12 }}>{error}</p>}

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
        <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>Back</Button>
        {step < STEPS.length - 1
          ? <Button onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))} disabled={step === 0 && form.title.trim().length < 2}>Next</Button>
          : <Button variant="ghost" onClick={() => navigate('/organizer')}>Done</Button>}
      </div>
    </div>
  );
}
