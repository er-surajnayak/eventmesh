// Reusable form primitives in the EventMesh design language (dark, CSS-var tokens).

const inputBase = {
  width: '100%',
  padding: '11px 13px',
  border: '1px solid var(--line-2)',
  borderRadius: 10,
  background: 'var(--bg-3)',
  color: 'var(--fg)',
  fontFamily: 'inherit',
  fontSize: 14,
  outline: 'none',
};

export function Field({ label, hint, children }) {
  return (
    <label style={{ display: 'block', marginBottom: 16 }}>
      {label && (
        <div style={{ fontSize: 12.5, color: 'var(--fg-2)', marginBottom: 7, fontWeight: 500 }}>
          {label}
        </div>
      )}
      {children}
      {hint && <div style={{ fontSize: 11.5, color: 'var(--fg-3)', marginTop: 6 }}>{hint}</div>}
    </label>
  );
}

export function TextInput({ value, onChange, ...rest }) {
  return (
    <input
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      style={inputBase}
      {...rest}
    />
  );
}

export function TextArea({ value, onChange, rows = 4, ...rest }) {
  return (
    <textarea
      value={value ?? ''}
      rows={rows}
      onChange={(e) => onChange(e.target.value)}
      style={{ ...inputBase, resize: 'vertical', lineHeight: 1.5 }}
      {...rest}
    />
  );
}

export function NumberInput({ value, onChange, ...rest }) {
  return (
    <input
      type="number"
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
      style={inputBase}
      {...rest}
    />
  );
}

export function DateTimeInput({ value, onChange }) {
  return (
    <input
      type="datetime-local"
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value || null)}
      style={{ ...inputBase, colorScheme: 'dark' }}
    />
  );
}

export function Segmented({ value, onChange, options }) {
  return (
    <div
      style={{
        display: 'inline-flex', padding: 3, borderRadius: 10, gap: 2,
        background: 'var(--bg-3)', border: '1px solid var(--line-2)', flexWrap: 'wrap',
      }}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            style={{
              padding: '7px 13px', borderRadius: 7, border: 'none',
              background: active ? 'rgba(0,214,255,0.12)' : 'transparent',
              color: active ? 'var(--accent)' : 'var(--fg-2)',
              fontSize: 12.5, fontWeight: active ? 600 : 400, cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export function Toggle({ checked, onChange, label }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      style={{
        display: 'flex', alignItems: 'center', gap: 10, background: 'none',
        border: 'none', cursor: 'pointer', padding: 0,
      }}
    >
      <span
        style={{
          width: 38, height: 22, borderRadius: 999, padding: 2, transition: 'background 0.2s',
          background: checked ? 'var(--accent)' : 'var(--bg-3)',
          border: '1px solid var(--line-2)',
        }}
      >
        <span
          style={{
            display: 'block', width: 16, height: 16, borderRadius: 999, background: checked ? '#000' : 'var(--fg-2)',
            transform: checked ? 'translateX(16px)' : 'none', transition: 'transform 0.2s',
          }}
        />
      </span>
      {label && <span style={{ fontSize: 13, color: 'var(--fg)' }}>{label}</span>}
    </button>
  );
}

export function Button({ variant = 'primary', children, style, ...rest }) {
  const variants = {
    primary: { background: 'var(--accent)', color: '#000', border: 'none', fontWeight: 600 },
    ghost: { background: 'transparent', color: 'var(--fg)', border: '1px solid var(--line-2)' },
    danger: { background: 'transparent', color: '#ff6b6b', border: '1px solid rgba(255,107,107,0.4)' },
  };
  return (
    <button
      style={{
        padding: '11px 18px', borderRadius: 999, fontSize: 13.5, cursor: 'pointer',
        fontFamily: 'inherit', transition: 'filter 0.15s, opacity 0.15s',
        ...variants[variant], ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}

const STATUS_COLORS = {
  draft: '#9aa0a6',
  preview: '#c084fc',
  pending_review: '#ffb84d',
  published: '#4ade80',
  hidden: '#7d8590',
  cancelled: '#ff6b6b',
  archived: '#5a5a5a',
};

export function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || 'var(--fg-3)';
  return (
    <span
      className="mono"
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 10, letterSpacing: '0.08em',
        textTransform: 'uppercase', color: 'var(--fg-2)', border: '1px solid var(--line)',
        padding: '3px 8px', borderRadius: 6, background: 'rgba(255,255,255,0.02)',
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: 99, background: color, boxShadow: `0 0 6px ${color}80` }} />
      {String(status).replace('_', ' ')}
    </span>
  );
}
