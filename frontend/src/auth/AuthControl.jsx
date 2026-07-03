import { useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { AuthModal } from './AuthModal';
import { ProtectedRoute } from './ProtectedRoute';
import { useProfile } from '../profile/useProfile';
import { api } from '../lib/apiClient';

const navBtn = {
  background: 'transparent',
  color: 'var(--fg)',
  border: '1px solid var(--line-2)',
  borderRadius: 999,
  padding: '8px 16px',
  fontSize: 13,
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'all 0.2s',
};

const primaryBtn = {
  width: '100%',
  padding: '10px 14px',
  border: 'none',
  borderRadius: 999,
  background: 'var(--accent)',
  color: '#000',
  fontSize: 13,
  fontWeight: 600,
  cursor: 'pointer',
};

const ghostBtn = {
  width: '100%',
  padding: '10px 14px',
  border: '1px solid var(--line-2)',
  borderRadius: 999,
  background: 'transparent',
  color: 'var(--fg)',
  fontSize: 13,
  cursor: 'pointer',
};

const inputStyle = {
  width: '100%',
  padding: '10px 12px',
  border: '1px solid var(--line-2)',
  borderRadius: 10,
  background: 'var(--bg-3)',
  color: 'var(--fg)',
  fontFamily: 'inherit',
  fontSize: 13.5,
  outline: 'none',
};

export function AuthControl() {
  const { isAuthenticated, user, loading, signOut } = useAuth();
  const [modalOpen, setModalOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  if (loading) return null;

  if (!isAuthenticated) {
    return (
      <>
        <button className="nav-explore-btn" style={navBtn} onClick={() => setModalOpen(true)}>
          Sign in
        </button>
        <AuthModal open={modalOpen} onClose={() => setModalOpen(false)} />
      </>
    );
  }

  const label = user?.email ? user.email.split('@')[0] : 'Account';

  return (
    <>
      <button
        className="nav-explore-btn"
        style={{ ...navBtn, display: 'flex', alignItems: 'center', gap: 8 }}
        onClick={() => setAccountOpen(true)}
        title={user?.email || ''}
      >
        <span
          style={{
            width: 22, height: 22, borderRadius: 999, background: 'var(--accent)',
            color: '#000', display: 'grid', placeItems: 'center', fontSize: 11, fontWeight: 700,
          }}
        >
          {label.charAt(0).toUpperCase()}
        </span>
        <span style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {label}
        </span>
      </button>
      <AccountPanel open={accountOpen} onClose={() => setAccountOpen(false)} onSignOut={signOut} />
    </>
  );
}

function AccountPanel({ open, onClose, onSignOut }) {
  if (!open) return null;
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 200, background: 'rgba(5,5,5,0.72)',
        backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)', display: 'grid',
        placeItems: 'center', padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 400, maxHeight: '85vh', overflowY: 'auto',
          background: 'var(--bg-2)', border: '1px solid var(--line-2)',
          borderRadius: 'var(--radius)', padding: 26, boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <div style={{ fontSize: 17, fontWeight: 600 }}>Your account</div>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{ background: 'none', border: 'none', color: 'var(--fg-3)', fontSize: 18, cursor: 'pointer' }}
          >
            ×
          </button>
        </div>
        <ProtectedRoute fallback={<p style={{ color: 'var(--fg-2)', fontSize: 13 }}>Please sign in.</p>}>
          <AccountDetails onSignOut={onSignOut} onClose={onClose} />
        </ProtectedRoute>
      </div>
    </div>
  );
}

function row(label, value) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '8px 0', borderBottom: '1px solid var(--line)' }}>
      <span style={{ fontSize: 12.5, color: 'var(--fg-3)' }}>{label}</span>
      <span className="mono" style={{ fontSize: 12.5, color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis' }}>{value}</span>
    </div>
  );
}

function AccountDetails({ onSignOut, onClose }) {
  const { profile, loading, error, becomeOrganizer } = useProfile();
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState('');

  const onBecomeOrganizer = async () => {
    setBusy(true);
    setActionError('');
    try {
      await becomeOrganizer();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (error) return <p style={{ fontSize: 12.5, color: '#ff6b6b' }}>Could not load profile: {error.message}</p>;
  if (loading || !profile) return <p style={{ fontSize: 13, color: 'var(--fg-2)' }}>Loading…</p>;

  return (
    <div>
      <div style={{ marginBottom: 18 }}>
        {row('Email', profile.email || '—')}
        {row('Role', profile.role)}
        {row('Organizer', profile.is_organizer ? 'Yes' : 'No')}
        {row('User ID', `${String(profile.id).slice(0, 8)}…`)}
      </div>

      {!profile.is_organizer ? (
        <div style={{ marginBottom: 18 }}>
          <p style={{ fontSize: 12.5, color: 'var(--fg-2)', margin: '0 0 10px' }}>
            Want to host events? Become an organizer to create an organization.
          </p>
          <button style={primaryBtn} disabled={busy} onClick={onBecomeOrganizer}>
            {busy ? 'Working…' : 'Become an organizer'}
          </button>
          {actionError && <p style={{ fontSize: 12, color: '#ff6b6b', marginTop: 8 }}>{actionError}</p>}
        </div>
      ) : (
        <OrganizationsSection />
      )}

      <button
        onClick={async () => { await onSignOut(); onClose(); }}
        style={{ ...ghostBtn, marginTop: 4 }}
      >
        Sign out
      </button>
    </div>
  );
}

function OrganizationsSection() {
  const [orgs, setOrgs] = useState(null);
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setOrgs(await api.listOrganizations());
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api.createOrganization({ name: name.trim() });
      setName('');
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ marginBottom: 18 }}>
      <div className="mono" style={{ fontSize: 10.5, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--fg-3)', marginBottom: 10 }}>
        Organizations
      </div>

      {orgs && orgs.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          {orgs.map((o) => (
            <div key={o.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--line)' }}>
              <span style={{ fontSize: 13, color: 'var(--fg)' }}>{o.name}</span>
              <span className="mono" style={{ fontSize: 11, color: 'var(--fg-3)' }}>{o.slug} · {o.role}</span>
            </div>
          ))}
        </div>
      )}
      {orgs && orgs.length === 0 && (
        <p style={{ fontSize: 12.5, color: 'var(--fg-2)', margin: '0 0 10px' }}>No organizations yet.</p>
      )}

      <form onSubmit={create} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <input
          required
          placeholder="Organization name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={inputStyle}
        />
        <button type="submit" style={primaryBtn} disabled={busy}>
          {busy ? 'Creating…' : 'Create organization'}
        </button>
      </form>
      {error && <p style={{ fontSize: 12, color: '#ff6b6b', marginTop: 8 }}>{error}</p>}
    </div>
  );
}
