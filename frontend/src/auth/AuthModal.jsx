import { useState } from 'react';
import { useAuth } from './useAuth';

const overlayStyle = {
  position: 'fixed',
  inset: 0,
  zIndex: 200,
  background: 'rgba(5,5,5,0.72)',
  backdropFilter: 'blur(6px)',
  WebkitBackdropFilter: 'blur(6px)',
  display: 'grid',
  placeItems: 'center',
  padding: 20,
};

const cardStyle = {
  width: '100%',
  maxWidth: 380,
  background: 'var(--bg-2)',
  border: '1px solid var(--line-2)',
  borderRadius: 'var(--radius)',
  padding: 26,
  boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
};

const inputStyle = {
  width: '100%',
  padding: '11px 14px',
  border: '1px solid var(--line-2)',
  borderRadius: 10,
  background: 'var(--bg-3)',
  color: 'var(--fg)',
  fontFamily: 'inherit',
  fontSize: 14,
  outline: 'none',
};

const primaryBtn = {
  width: '100%',
  padding: '12px 16px',
  border: 'none',
  borderRadius: 999,
  background: 'var(--accent)',
  color: '#000',
  fontSize: 14,
  fontWeight: 600,
  cursor: 'pointer',
};

const ghostBtn = {
  width: '100%',
  padding: '11px 16px',
  border: '1px solid var(--line-2)',
  borderRadius: 999,
  background: 'transparent',
  color: 'var(--fg)',
  fontSize: 13.5,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 10,
};

export function AuthModal({ open, onClose }) {
  const { signInWithOtp, verifyOtp, signInWithGoogle } = useAuth();
  const [step, setStep] = useState('email'); // 'email' | 'code'
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  if (!open) return null;

  const reset = () => {
    setStep('email');
    setCode('');
    setError('');
    setNotice('');
    setBusy(false);
  };
  const close = () => {
    reset();
    onClose();
  };

  const sendCode = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    const { error: err } = await signInWithOtp(email.trim());
    setBusy(false);
    if (err) {
      setError(err.message);
      return;
    }
    setStep('code');
    setNotice(`We sent a 6-digit code to ${email.trim()}.`);
  };

  const confirmCode = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    const { error: err } = await verifyOtp(email.trim(), code.trim());
    setBusy(false);
    if (err) {
      setError(err.message);
      return;
    }
    close();
  };

  const google = async () => {
    setError('');
    const { error: err } = await signInWithGoogle();
    if (err) setError(err.message);
  };

  return (
    <div style={overlayStyle} onClick={close}>
      <div style={cardStyle} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
          <div style={{ fontSize: 17, fontWeight: 600 }}>Sign in to EventMesh</div>
          <button
            onClick={close}
            aria-label="Close"
            style={{ background: 'none', border: 'none', color: 'var(--fg-3)', fontSize: 18, cursor: 'pointer' }}
          >
            ×
          </button>
        </div>
        <p style={{ margin: '0 0 20px', fontSize: 13, color: 'var(--fg-2)' }}>
          No passwords — we&apos;ll email you a one-time code.
        </p>

        <button style={ghostBtn} onClick={google}>
          <span aria-hidden style={{ fontWeight: 700 }}>G</span>
          Continue with Google
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '18px 0' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--line)' }} />
          <span className="mono" style={{ fontSize: 10.5, color: 'var(--fg-3)', letterSpacing: '0.1em' }}>OR</span>
          <div style={{ flex: 1, height: 1, background: 'var(--line)' }} />
        </div>

        {step === 'email' ? (
          <form onSubmit={sendCode} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input
              type="email"
              required
              autoFocus
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputStyle}
            />
            <button type="submit" style={primaryBtn} disabled={busy}>
              {busy ? 'Sending…' : 'Send code'}
            </button>
          </form>
        ) : (
          <form onSubmit={confirmCode} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input
              inputMode="numeric"
              required
              autoFocus
              placeholder="6-digit code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={{ ...inputStyle, letterSpacing: '0.3em', textAlign: 'center' }}
            />
            <button type="submit" style={primaryBtn} disabled={busy}>
              {busy ? 'Verifying…' : 'Verify & sign in'}
            </button>
            <button
              type="button"
              onClick={() => { setStep('email'); setError(''); setNotice(''); }}
              style={{ background: 'none', border: 'none', color: 'var(--fg-3)', fontSize: 12.5, cursor: 'pointer' }}
            >
              ← Use a different email
            </button>
          </form>
        )}

        {notice && <p style={{ margin: '14px 0 0', fontSize: 12.5, color: 'var(--accent)' }}>{notice}</p>}
        {error && <p style={{ margin: '14px 0 0', fontSize: 12.5, color: '#ff6b6b' }}>{error}</p>}
      </div>
    </div>
  );
}
