import { useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { AuthModal } from './AuthModal';
import { ProtectedRoute } from './ProtectedRoute';
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
          width: '100%', maxWidth: 380, background: 'var(--bg-2)', border: '1px solid var(--line-2)',
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

function AccountDetails({ onSignOut, onClose }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    api
      .getMe()
      .then((data) => mounted && setProfile(data))
      .catch((err) => mounted && setError(err.message));
    return () => { mounted = false; };
  }, []);

  const row = (label, value) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '8px 0', borderBottom: '1px solid var(--line)' }}>
      <span style={{ fontSize: 12.5, color: 'var(--fg-3)' }}>{label}</span>
      <span className="mono" style={{ fontSize: 12.5, color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis' }}>{value}</span>
    </div>
  );

  return (
    <div>
      {error && <p style={{ fontSize: 12.5, color: '#ff6b6b' }}>Could not load profile: {error}</p>}
      {!error && !profile && <p style={{ fontSize: 13, color: 'var(--fg-2)' }}>Loading…</p>}
      {profile && (
        <div style={{ marginBottom: 18 }}>
          {row('Email', profile.email || '—')}
          {row('Role', profile.role)}
          {row('Organizer', profile.is_organizer ? 'Yes' : 'No')}
          {row('User ID', `${String(profile.id).slice(0, 8)}…`)}
        </div>
      )}
      <button
        onClick={async () => { await onSignOut(); onClose(); }}
        style={{
          width: '100%', padding: '11px 16px', border: '1px solid var(--line-2)', borderRadius: 999,
          background: 'transparent', color: 'var(--fg)', fontSize: 13.5, cursor: 'pointer',
        }}
      >
        Sign out
      </button>
    </div>
  );
}
