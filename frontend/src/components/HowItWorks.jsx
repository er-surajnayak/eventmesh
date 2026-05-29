import React from 'react';
import { StaticMesh } from './StaticMesh';

export function HowItWorks({ tweaks }) {
  return (
    <section id="how" style={{ padding: '120px 0', borderTop: '1px solid var(--line)', background: 'var(--bg)', position: 'relative' }}>
      <div className="container">
        <div className="mono reveal" style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--fg-3)', marginBottom: 14 }}>
          / 03 — How it works
        </div>
        <h2 className="reveal" style={{ margin: 0, fontSize: 'clamp(30px, 4vw, 52px)', letterSpacing: '-0.024em', fontWeight: 600, lineHeight: 1.05, maxWidth: 820, textWrap: 'balance' }}>
          Every platform. <span style={{ color: 'var(--fg-3)' }}>One mesh.</span>
        </h2>
        <p className="reveal" style={{ margin: '18px 0 64px', fontSize: 16, color: 'var(--fg-2)', maxWidth: 580, lineHeight: 1.6 }}>
          We pull live feeds, normalize them into a shared schema, and surface one
          unified discovery surface. Links always route back to the source.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 32, alignItems: 'center' }} className="how-grid">
          <div className="reveal" style={{
            background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 18,
            padding: 24, minHeight: 320, position: 'relative', overflow: 'hidden',
          }}>
            <div className="mono" style={{ fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--fg-3)', marginBottom: 8 }}>
              Before
            </div>
            <div style={{ fontSize: 18, fontWeight: 500, marginBottom: 18 }}>Scattered across platforms</div>
            <div style={{ height: 220 }}>
              <StaticMesh scattered={true} accent={tweaks.accent} width={420} height={240} />
            </div>
            {[
              { l: 'Eventbrite', x: 16, y: 62 },
              { l: 'Meetup', x: 78, y: 62 },
              { l: 'Luma', x: 16, y: 22 },
              { l: '…', x: 78, y: 22 },
            ].map((p, i) => (
              <span key={i} className="mono" style={{
                position: 'absolute', top: `${100 - p.y}%`, left: `${p.x}%`,
                fontSize: 10, color: 'var(--fg-3)', letterSpacing: '0.08em', textTransform: 'uppercase',
                transform: 'translate(-50%, -50%)', pointerEvents: 'none',
              }}>{p.l}</span>
            ))}
          </div>

          <div className="reveal" style={{ display: 'grid', placeItems: 'center', color: tweaks.accent }}>
            <svg width="72" height="48" viewBox="0 0 72 48" fill="none">
              <path d="M4 24h60M52 10l14 14-14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="4" cy="24" r="3" fill="currentColor" />
            </svg>
          </div>

          <div className="reveal" style={{
            background: `radial-gradient(circle at 50% 50%, ${tweaks.accent}10, var(--bg-2) 70%)`,
            border: `1px solid ${tweaks.accent}40`, borderRadius: 18,
            padding: 24, minHeight: 320, position: 'relative', overflow: 'hidden',
            boxShadow: `0 0 60px -10px ${tweaks.accent}22 inset`,
          }}>
            <div className="mono" style={{ fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: tweaks.accent, marginBottom: 8 }}>
              After
            </div>
            <div style={{ fontSize: 18, fontWeight: 500, marginBottom: 18 }}>Unified in EventMesh</div>
            <div style={{ height: 220 }}>
              <StaticMesh scattered={false} accent={tweaks.accent} width={420} height={240} />
            </div>
          </div>
        </div>

        <div style={{ marginTop: 80, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 2, borderRadius: 16, overflow: 'hidden', border: '1px solid var(--line)' }}>
          {[
            { n: '01', t: 'Fetch', d: 'Poll public APIs from Eventbrite, Meetup, and Luma every 15 minutes.' },
            { n: '02', t: 'Normalize', d: 'Map each source to a shared schema — title, venue, price, category.' },
            { n: '03', t: 'Surface', d: 'Serve a single live feed with filters, search, and deep-links back to source.' },
          ].map(step => (
            <div key={step.n} className="reveal" style={{ padding: '28px 24px', background: 'var(--bg-2)' }}>
              <div className="mono" style={{ fontSize: 11, letterSpacing: '0.14em', color: tweaks.accent, marginBottom: 14 }}>{step.n}</div>
              <div style={{ fontSize: 17, fontWeight: 500, marginBottom: 8 }}>{step.t}</div>
              <div style={{ fontSize: 13.5, color: 'var(--fg-2)', lineHeight: 1.55 }}>{step.d}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
