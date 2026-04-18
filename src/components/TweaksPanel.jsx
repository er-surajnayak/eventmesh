import React from 'react';

export function TweaksPanel({ tweaks, setTweaks, visible }) {
  if (!visible) return null;
  const set = (k, v) => setTweaks(t => ({ ...t, [k]: v }));

  const swatches = [
    { c: '#00D6FF', name: 'Cyan' },
    { c: '#0050FF', name: 'Cobalt' },
    { c: '#A78BFA', name: 'Violet' },
    { c: '#4ADE80', name: 'Lime' },
    { c: '#FF5E8A', name: 'Rose' },
    { c: '#FFB84D', name: 'Amber' },
  ];

  return (
    <div style={{
      position: 'fixed', right: 20, bottom: 20, zIndex: 100,
      width: 280,
      background: 'rgba(10,10,12,0.92)', backdropFilter: 'blur(18px) saturate(1.2)',
      border: '1px solid var(--line-2)', borderRadius: 14,
      padding: 16,
      boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
      fontFamily: 'Inter',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div className="mono" style={{ fontSize: 10.5, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--fg-2)' }}>
          Tweaks
        </div>
        <span style={{ width: 6, height: 6, borderRadius: 99, background: tweaks.accent, boxShadow: `0 0 8px ${tweaks.accent}` }} />
      </div>

      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 11, color: 'var(--fg-3)', marginBottom: 8, letterSpacing: '0.04em' }}>Accent color</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 6 }}>
          {swatches.map(s => (
            <button key={s.c} onClick={() => set('accent', s.c)} title={s.name} style={{
              aspectRatio: '1', borderRadius: 8,
              background: s.c,
              border: tweaks.accent === s.c ? '2px solid white' : '1px solid rgba(255,255,255,0.12)',
              boxShadow: tweaks.accent === s.c ? `0 0 0 2px ${s.c}55` : 'none',
              cursor: 'pointer',
            }} />
          ))}
        </div>
      </div>

      <SliderRow label="Mesh intensity" value={tweaks.meshIntensity} min={0} max={1.2} step={0.05} onChange={v => set('meshIntensity', v)} format={v => v.toFixed(2)} />
      <SliderRow label="Mesh density" value={tweaks.meshDensity} min={0.3} max={2} step={0.1} onChange={v => set('meshDensity', v)} format={v => v.toFixed(1) + '×'} />

      <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--line)' }}>
        <button onClick={() => setTweaks({
          accent: '#00D6FF', meshIntensity: 0.85, meshDensity: 1,
        })} style={{
          width: '100%', padding: '8px 10px', borderRadius: 8,
          background: 'transparent', border: '1px solid var(--line-2)',
          color: 'var(--fg-2)', fontSize: 12, cursor: 'pointer',
        }}>Reset</button>
      </div>
    </div>
  );
}

function SliderRow({ label, value, min, max, step, onChange, format }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 6 }}>
        <span style={{ color: 'var(--fg-3)' }}>{label}</span>
        <span className="mono" style={{ color: 'var(--fg-2)' }}>{format(value)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: 'var(--accent)' }}
      />
    </div>
  );
}
