import React, { useState } from 'react';
import { Icon, PlatformBadge, PriceTag } from './UIPrimitives';
import { formatEventDate } from '../utils/formatDate';

export function EventCard({ event, index = 0 }) {
  const [hover, setHover] = useState(false);
  return (
    <a
      href={event.url}
      target="_blank"
      rel="noopener noreferrer"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className="reveal"
      style={{
        display: 'block',
        position: 'relative',
        background: hover ? 'var(--bg-3)' : 'var(--bg-2)',
        border: `1px solid ${hover ? 'rgba(0,214,255,0.35)' : 'var(--line)'}`,
        borderRadius: 'var(--radius)',
        padding: 0,
        overflow: 'hidden',
        transform: hover ? 'translateY(-4px)' : 'none',
        boxShadow: hover
          ? '0 14px 40px -10px rgba(0,214,255,0.18), 0 2px 0 rgba(255,255,255,0.03) inset'
          : '0 1px 0 rgba(255,255,255,0.02) inset',
        transition: 'all 0.35s cubic-bezier(.2,.8,.2,1)',
        transitionDelay: `${Math.min(index * 30, 240)}ms`,
      }}
    >
      <div style={{
        position: 'relative',
        height: 140,
        background: `linear-gradient(135deg, oklch(0.28 0.08 ${event.hue}) 0%, oklch(0.14 0.05 ${event.hue}) 100%)`,
        overflow: 'hidden',
        borderBottom: '1px solid var(--line)',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,0.04) 0 1px, transparent 1px 14px)',
        }} />
        <svg viewBox="0 0 100 100" style={{ position: 'absolute', right: -10, bottom: -10, width: 120, height: 120, opacity: 0.5 }}>
          <g stroke="rgba(255,255,255,0.35)" fill="none" strokeWidth="0.5">
            <circle cx="50" cy="50" r="48" />
            <circle cx="50" cy="50" r="34" />
            <circle cx="50" cy="50" r="20" />
            <line x1="2" y1="50" x2="98" y2="50" />
            <line x1="50" y1="2" x2="50" y2="98" />
          </g>
          <circle cx="50" cy="50" r="3" fill="rgba(255,255,255,0.7)" />
        </svg>
        <div className="mono" style={{
          position: 'absolute', top: 12, left: 14,
          fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase',
          color: 'rgba(255,255,255,0.85)',
        }}>
          {event.category}
        </div>
        <div className="mono" style={{
          position: 'absolute', top: 12, right: 14,
          display: 'flex', alignItems: 'center', gap: 5,
          fontSize: 10.5, color: 'rgba(255,255,255,0.72)',
        }}>
          {Icon.users}
          <span>{event.attendees}</span>
        </div>
        <div style={{
          position: 'absolute', bottom: 12, right: 14,
          width: 30, height: 30, borderRadius: 8,
          background: hover ? 'var(--accent)' : 'rgba(0,0,0,0.5)',
          border: '1px solid rgba(255,255,255,0.15)',
          display: 'grid', placeItems: 'center',
          color: hover ? '#000' : 'var(--fg)',
          transition: 'all 0.3s',
        }}>
          {Icon.external}
        </div>
      </div>

      <div style={{ padding: '18px 20px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
          <PlatformBadge platform={event.platform} />
          <PriceTag price={event.price} />
        </div>
        <h3 style={{
          margin: 0, fontSize: 17, fontWeight: 600, lineHeight: 1.3,
          letterSpacing: '-0.012em', color: 'var(--fg)',
          textWrap: 'balance',
        }}>{event.title}</h3>
        <p style={{
          margin: '10px 0 0', fontSize: 13, lineHeight: 1.55, color: 'var(--fg-2)',
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
        }}>{event.blurb}</p>
        <div style={{
          marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--line)',
          display: 'flex', flexDirection: 'column', gap: 7,
          fontSize: 12.5, color: 'var(--fg-2)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: 'var(--fg-3)' }}>{Icon.calendar}</span>
            <span>{formatEventDate(event.date)}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: 'var(--fg-3)' }}>{Icon.pin}</span>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{event.venue}</span>
          </div>
        </div>
      </div>
    </a>
  );
}

export function SkeletonCard() {
  return (
    <div style={{
      background: 'var(--bg-2)', border: '1px solid var(--line)',
      borderRadius: 'var(--radius)', overflow: 'hidden',
    }}>
      <div style={{ height: 140, background: 'linear-gradient(90deg, #0f0f12, #15151a, #0f0f12)', backgroundSize: '200% 100%', animation: 'shimmer 1.6s infinite' }} />
      <div style={{ padding: 20 }}>
        <div style={{ height: 10, width: '40%', background: '#15151a', borderRadius: 4, marginBottom: 12 }} />
        <div style={{ height: 14, width: '85%', background: '#17171c', borderRadius: 4, marginBottom: 8 }} />
        <div style={{ height: 14, width: '65%', background: '#17171c', borderRadius: 4 }} />
      </div>
    </div>
  );
}
