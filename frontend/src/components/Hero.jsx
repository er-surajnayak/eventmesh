import React from 'react';
import { MeshBackground } from './MeshBackground';
import { Icon } from './UIPrimitives';

export function Hero({ onExplore, tweaks }) {
  return (
    <section id="top" style={{
      position: 'relative',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      overflow: 'hidden',
      borderBottom: '1px solid var(--line)',
    }}>
      <div style={{ position: 'absolute', inset: 0 }}>
        <MeshBackground 
          intensity={tweaks.meshIntensity} 
          accent={tweaks.accent} 
          interactive={true} 
          density={tweaks.meshDensity} 
        />
      </div>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at center, transparent 0%, rgba(5,5,5,0.4) 70%, var(--bg) 100%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', left: 0, right: 0, bottom: 0, height: 160,
        background: 'linear-gradient(to bottom, transparent, var(--bg))',
        pointerEvents: 'none',
      }} />

      <div className="container" style={{ position: 'relative', zIndex: 2, paddingTop: 120, paddingBottom: 120 }}>
        <div className="mono" style={{
          display: 'inline-flex', alignItems: 'center', gap: 10,
          padding: '6px 12px', borderRadius: 999,
          border: '1px solid var(--line-2)',
          background: 'rgba(10,10,12,0.5)',
          backdropFilter: 'blur(8px)',
          fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase',
          color: 'var(--fg-2)',
          marginBottom: 28,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: 99, background: tweaks.accent, boxShadow: `0 0 10px ${tweaks.accent}` }} />
          Live · 3 sources · 2,184 events
        </div>

        <h1 style={{
          fontSize: 'clamp(40px, 6.2vw, 84px)',
          lineHeight: 1.02,
          letterSpacing: '-0.03em',
          fontWeight: 600,
          margin: 0,
          maxWidth: 980,
          textWrap: 'balance',
        }}>
          Discover events from{' '}
          <span style={{ color: tweaks.accent, textShadow: `0 0 40px ${tweaks.accent}55` }}>everywhere</span>{' '}
          in one place
        </h1>

        <p style={{
          marginTop: 26, fontSize: 'clamp(16px, 1.4vw, 19px)', lineHeight: 1.55,
          color: 'var(--fg-2)', maxWidth: 620, fontWeight: 300,
        }}>
          EventMesh aggregates events from Eventbrite, Meetup, and Luma into one
          unified feed — search, filter, and jump straight to the source.
        </p>

        <div style={{ marginTop: 40, display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
          <button onClick={onExplore} style={{
            background: tweaks.accent, color: '#000',
            border: 'none', borderRadius: 999,
            padding: '14px 22px', fontSize: 14.5, fontWeight: 600,
            display: 'inline-flex', alignItems: 'center', gap: 8,
            boxShadow: `0 10px 30px -6px ${tweaks.accent}66`,
            transition: 'transform 0.2s, box-shadow 0.2s',
          }}>
            Explore events {Icon.arrow}
          </button>
          <a href="#how" style={{
            padding: '14px 18px', fontSize: 14, color: 'var(--fg-2)',
            border: '1px solid var(--line-2)', borderRadius: 999,
            background: 'rgba(10,10,12,0.4)', backdropFilter: 'blur(8px)',
            transition: 'all 0.2s',
          }}>
            How it works
          </a>
        </div>

        <div style={{ marginTop: 72, display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
          <span className="mono" style={{ fontSize: 10.5, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--fg-3)' }}>
            Aggregating from
          </span>
          {['Eventbrite', 'Meetup', 'Luma'].map(p => (
            <div key={p} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '7px 14px', borderRadius: 8,
              border: '1px solid var(--line)',
              background: 'rgba(10,10,12,0.5)', backdropFilter: 'blur(8px)',
              fontSize: 13, color: 'var(--fg-2)',
            }}>
              <span style={{ width: 6, height: 6, borderRadius: 99, background: {Eventbrite:'#FF8A65',Meetup:'#FF4D4D',Luma:'#C084FC'}[p] }} />
              {p}
            </div>
          ))}
        </div>
      </div>

      <div style={{
        position: 'absolute', bottom: 26, left: '50%', transform: 'translateX(-50%)',
        color: 'var(--fg-3)', fontSize: 11, display: 'flex', flexDirection: 'column',
        alignItems: 'center', gap: 6, zIndex: 2,
      }} className="mono">
        <span style={{ letterSpacing: '0.18em' }}>SCROLL</span>
        <span style={{ animation: 'bob 1.8s ease-in-out infinite' }}>{Icon.chevron}</span>
      </div>
    </section>
  );
}
