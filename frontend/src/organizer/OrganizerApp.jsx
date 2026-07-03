import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, Route, Routes } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';
import { useProfile } from '../profile/useProfile';
import { api } from '../lib/apiClient';
import { LogoMark } from '../components/UIPrimitives';
import { Button } from './components/fields';
import { OrganizerContext } from './OrganizerContext';
import { OrganizerDashboard } from './OrganizerDashboard';
import { EventWizard } from './EventWizard';
import { EventPreview } from './EventPreview';

function Centered({ children }) {
  return (
    <div style={{ minHeight: '70vh', display: 'grid', placeItems: 'center', padding: 24 }}>
      <div style={{ textAlign: 'center', maxWidth: 420 }}>{children}</div>
    </div>
  );
}

function TopBar({ orgs, currentSlug, onSelectOrg }) {
  return (
    <header
      style={{
        position: 'sticky', top: 0, zIndex: 40, borderBottom: '1px solid var(--line)',
        background: 'rgba(5,5,5,0.82)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)',
      }}
    >
      <div
        className="container org-topbar"
        style={{ display: 'flex', alignItems: 'center', gap: 16, height: 60 }}
      >
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <LogoMark size={20} />
          <span style={{ fontSize: 14.5, fontWeight: 600 }}>EventMesh</span>
        </Link>
        <span className="mono" style={{ fontSize: 11, color: 'var(--fg-3)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
          / Organizer
        </span>
        <div style={{ flex: 1 }} />
        {orgs && orgs.length > 0 && (
          <select
            value={currentSlug || ''}
            onChange={(e) => onSelectOrg(e.target.value)}
            style={{
              padding: '8px 12px', borderRadius: 10, background: 'var(--bg-2)',
              border: '1px solid var(--line-2)', color: 'var(--fg)', fontSize: 13, fontFamily: 'inherit',
            }}
          >
            {orgs.map((o) => (
              <option key={o.id} value={o.slug}>{o.name}</option>
            ))}
          </select>
        )}
        <Link to="/" style={{ fontSize: 13, color: 'var(--fg-2)' }}>← Back to site</Link>
      </div>
    </header>
  );
}

export function OrganizerApp() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { profile, loading: profileLoading, becomeOrganizer } = useProfile();
  const [orgs, setOrgs] = useState(null);
  const [currentSlug, setCurrentSlug] = useState(null);
  const [busy, setBusy] = useState(false);

  const reloadOrgs = useCallback(async () => {
    const list = await api.listOrganizations();
    setOrgs(list);
    setCurrentSlug((prev) => prev || (list[0]?.slug ?? null));
    return list;
  }, []);

  useEffect(() => {
    if (profile?.is_organizer) reloadOrgs().catch(() => setOrgs([]));
  }, [profile?.is_organizer, reloadOrgs]);

  const currentOrg = useMemo(
    () => (orgs || []).find((o) => o.slug === currentSlug) || null,
    [orgs, currentSlug],
  );

  const ctxValue = useMemo(
    () => ({ orgs: orgs || [], currentOrg, currentSlug, setCurrentSlug, reloadOrgs }),
    [orgs, currentOrg, currentSlug, reloadOrgs],
  );

  if (authLoading || profileLoading) {
    return <Centered><p style={{ color: 'var(--fg-2)' }}>Loading…</p></Centered>;
  }

  if (!isAuthenticated) {
    return (
      <Centered>
        <h2 style={{ margin: '0 0 12px', fontWeight: 600 }}>Sign in to continue</h2>
        <p style={{ color: 'var(--fg-2)', fontSize: 14, marginBottom: 20 }}>
          The organizer dashboard requires an account.
        </p>
        <Link to="/"><Button>Go to sign in</Button></Link>
      </Centered>
    );
  }

  if (!profile?.is_organizer) {
    return (
      <Centered>
        <h2 style={{ margin: '0 0 12px', fontWeight: 600 }}>Become an organizer</h2>
        <p style={{ color: 'var(--fg-2)', fontSize: 14, marginBottom: 20 }}>
          Host events on EventMesh — it only takes a click.
        </p>
        <Button
          disabled={busy}
          onClick={async () => { setBusy(true); try { await becomeOrganizer(); } finally { setBusy(false); } }}
        >
          {busy ? 'Working…' : 'Become an organizer'}
        </Button>
      </Centered>
    );
  }

  return (
    <OrganizerContext.Provider value={ctxValue}>
      <TopBar orgs={orgs} currentSlug={currentSlug} onSelectOrg={setCurrentSlug} />
      <main className="container" style={{ padding: '28px 32px 80px' }}>
        <Routes>
          <Route index element={<OrganizerDashboard />} />
          <Route path="events/new" element={<EventWizard key="new" mode="create" />} />
          <Route path="events/:eventId/edit" element={<EventWizard mode="edit" />} />
          <Route path="events/:eventId/preview" element={<EventPreview />} />
        </Routes>
      </main>
    </OrganizerContext.Provider>
  );
}
