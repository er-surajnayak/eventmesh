import React from 'react';

export function SourcesStrip({ tweaks }) {
  const sources = [
    { name: 'Eventbrite', count: 1842, color: '#FF8A65' },
    { name: 'Meetup', count: 1240, color: '#FF4D4D' },
    { name: 'Luma', count: 856, color: '#C084FC' },
    { name: 'Partiful', count: 420, color: '#FFD700' },
  ];
  return (
    <section id="sources" style={{ padding: '80px 0', borderTop: '1px solid var(--line)', background: 'var(--bg-2)' }}>
      <div className="container">
        <div className="mono reveal" style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--fg-3)', marginBottom: 14 }}>
          / 04 — Sources
        </div>
        <h2 className="reveal" style={{ margin: 0, fontSize: 'clamp(24px, 2.8vw, 34px)', letterSpacing: '-0.02em', fontWeight: 600, marginBottom: 40 }}>
          Live from <span style={{ color: tweaks.accent }}>{sources.reduce((s, x) => s + x.count, 0).toLocaleString()}</span> events across {sources.length} platforms.
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          {sources.map(s => (
            <div key={s.name} className="reveal" style={{
              background: 'var(--bg-3)', border: '1px solid var(--line)',
              borderRadius: 12, padding: 22, display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <div style={{
                width: 44, height: 44, borderRadius: 10,
                background: `${s.color}15`, border: `1px solid ${s.color}50`,
                display: 'grid', placeItems: 'center',
              }}>
                <span style={{ width: 10, height: 10, borderRadius: 99, background: s.color, boxShadow: `0 0 12px ${s.color}` }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 15, fontWeight: 500 }}>{s.name}</div>
                <div className="mono" style={{ fontSize: 12, color: 'var(--fg-3)', marginTop: 4 }}>
                  {s.count.toLocaleString()} live events
                </div>
              </div>
              <span style={{ width: 6, height: 6, borderRadius: 99, background: '#4ade80', boxShadow: '0 0 8px #4ade80' }} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
