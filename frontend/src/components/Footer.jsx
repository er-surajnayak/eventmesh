import React from 'react';
import { LogoMark } from './UIPrimitives';

export function Footer() {
  return (
    <footer style={{ borderTop: '1px solid var(--line)', background: 'var(--bg)', padding: '48px 0 40px' }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <LogoMark size={18} />
          <span style={{ fontSize: 13.5, fontWeight: 500 }}>EventMesh</span>
          <span className="mono" style={{ fontSize: 11, color: 'var(--fg-3)', marginLeft: 10 }}>v0.4.0</span>
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--fg-3)' }}>
          Built by <span style={{ color: 'var(--fg-2)' }}>NayakLabs</span> · © 2026
        </div>
      </div>
    </footer>
  );
}
