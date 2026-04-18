import React from 'react';

// Icon set (thin line, stroke 1.5)
export const Icon = {
  search: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
    </svg>
  ),
  pin: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>
    </svg>
  ),
  calendar: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>
    </svg>
  ),
  clock: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>
    </svg>
  ),
  users: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 20v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  arrow: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M13 5l7 7-7 7"/>
    </svg>
  ),
  external: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 17 17 7M8 7h9v9"/>
    </svg>
  ),
  x: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M18 6 6 18M6 6l12 12"/>
    </svg>
  ),
  chevron: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="m6 9 6 6 6-6"/>
    </svg>
  ),
};

export function LogoMark({ size = 22, accent = 'var(--accent)' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ display: 'block' }}>
      <g stroke={accent} strokeWidth="1" fill="none" opacity="0.9">
        <line x1="4" y1="5" x2="12" y2="12" />
        <line x1="20" y1="5" x2="12" y2="12" />
        <line x1="4" y1="19" x2="12" y2="12" />
        <line x1="20" y1="19" x2="12" y2="12" />
        <line x1="4" y1="5" x2="4" y2="19" />
        <line x1="20" y1="5" x2="20" y2="19" />
      </g>
      <g fill={accent}>
        <circle cx="12" cy="12" r="2.2" />
      </g>
      <g fill="rgba(255,255,255,0.95)">
        <circle cx="4" cy="5" r="1.4" />
        <circle cx="20" cy="5" r="1.4" />
        <circle cx="4" cy="19" r="1.4" />
        <circle cx="20" cy="19" r="1.4" />
      </g>
    </svg>
  );
}

export function PlatformBadge({ platform }) {
  const dotColor = {
    Eventbrite: '#FF8A65',
    Meetup: '#FF4D4D',
    Luma: '#C084FC',
  }[platform] || '#888';
  return (
    <span className="mono" style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      fontSize: 10.5, letterSpacing: '0.08em', textTransform: 'uppercase',
      color: 'var(--fg-2)',
      border: '1px solid var(--line)',
      padding: '4px 8px', borderRadius: 6,
      background: 'rgba(255,255,255,0.02)',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: 99, background: dotColor, boxShadow: `0 0 6px ${dotColor}80` }} />
      {platform}
    </span>
  );
}

export function PriceTag({ price }) {
  const free = price === 'Free';
  return (
    <span className="mono" style={{
      fontSize: 10.5, letterSpacing: '0.05em',
      color: free ? 'var(--accent)' : 'var(--fg)',
      padding: '4px 8px',
      borderRadius: 6,
      border: `1px solid ${free ? 'rgba(0,214,255,0.3)' : 'var(--line)'}`,
      background: free ? 'rgba(0,214,255,0.06)' : 'rgba(255,255,255,0.02)',
      textTransform: 'uppercase',
    }}>{price}</span>
  );
}
