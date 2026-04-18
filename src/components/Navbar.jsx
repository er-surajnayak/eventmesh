import React, { useState, useEffect } from 'react';
import { LogoMark } from './UIPrimitives';

export function Navbar({ onExplore }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
      backdropFilter: scrolled ? 'blur(14px) saturate(1.2)' : 'none',
      WebkitBackdropFilter: scrolled ? 'blur(14px) saturate(1.2)' : 'none',
      background: scrolled ? 'rgba(5,5,5,0.72)' : 'transparent',
      borderBottom: scrolled ? '1px solid var(--line)' : '1px solid transparent',
      transition: 'background 0.3s, border-color 0.3s',
    }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', height: 64, gap: 24 }}>
        <a href="#top" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <LogoMark size={22} />
          <span style={{ fontSize: 15, fontWeight: 600, letterSpacing: '-0.01em' }}>EventMesh</span>
        </a>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 28, fontSize: 13.5, color: 'var(--fg-2)' }} className="nav-links">
          <a href="#discover" style={{ transition: 'color 0.2s' }}>Discover</a>
          <a href="#how" style={{ transition: 'color 0.2s' }}>How it works</a>
          <a href="#sources" style={{ transition: 'color 0.2s' }}>Sources</a>
        </div>
        <button className="nav-explore-btn" onClick={onExplore} style={{
          background: 'transparent', color: 'var(--fg)',
          border: '1px solid var(--line-2)', borderRadius: 999,
          padding: '8px 16px', fontSize: 13, fontWeight: 500,
          transition: 'all 0.2s',
        }}>
          Explore events →
        </button>
      </div>
    </nav>
  );
}
