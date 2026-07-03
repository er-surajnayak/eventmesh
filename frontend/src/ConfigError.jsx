// Shown when required build-time env vars are missing (e.g. a Vercel build
// without VITE_SUPABASE_* set). Replaces a hard crash with a clear message.

const REQUIRED = [
  { key: 'VITE_SUPABASE_URL', present: Boolean(import.meta.env.VITE_SUPABASE_URL) },
  { key: 'VITE_SUPABASE_ANON_KEY', present: Boolean(import.meta.env.VITE_SUPABASE_ANON_KEY) },
  { key: 'VITE_API_BASE_URL', present: Boolean(import.meta.env.VITE_API_BASE_URL) },
];

export function ConfigError() {
  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24 }}>
      <div
        style={{
          maxWidth: 480, width: '100%', background: 'var(--bg-2)', border: '1px solid var(--line-2)',
          borderRadius: 'var(--radius)', padding: 30,
        }}
      >
        <div className="mono" style={{ fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#ffb84d', marginBottom: 14 }}>
          Configuration required
        </div>
        <h1 style={{ margin: '0 0 10px', fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em' }}>
          EventMesh isn&apos;t configured
        </h1>
        <p style={{ margin: '0 0 20px', fontSize: 14, color: 'var(--fg-2)', lineHeight: 1.6 }}>
          Required environment variables are missing from this build. Set them in your hosting
          provider (Vercel → Project → Settings → Environment Variables) and redeploy.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {REQUIRED.map(({ key, present }) => (
            <div
              key={key}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 12px', borderRadius: 10, background: 'var(--bg-3)',
                border: '1px solid var(--line)',
              }}
            >
              <span className="mono" style={{ fontSize: 12.5, color: 'var(--fg)' }}>{key}</span>
              <span
                className="mono"
                style={{ fontSize: 10.5, letterSpacing: '0.06em', color: present ? '#4ade80' : '#ff6b6b' }}
              >
                {present ? 'SET' : 'MISSING'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
