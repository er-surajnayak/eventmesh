import React, { useState, useEffect } from 'react';
import { EventCard, SkeletonCard } from './EventCard';
import { StaticMesh } from './StaticMesh';

export function EventGridSection({ filters, setFilters, events, loading }) {
  return (
    <section id="discover" style={{ padding: '56px 0 96px', background: 'var(--bg)' }}>
      <div className="container">
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 28, gap: 20, flexWrap: 'wrap' }}>
          <div>
            <div className="mono" style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--fg-3)', marginBottom: 10 }}>
              / 02 — Discover
            </div>
            <h2 style={{ margin: 0, fontSize: 'clamp(28px, 3.4vw, 42px)', letterSpacing: '-0.02em', fontWeight: 600, lineHeight: 1.1 }}>
              One feed, every platform.
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: 14.5, color: 'var(--fg-2)', maxWidth: 420, lineHeight: 1.55 }}>
            Cards link out to the original event page — we never get in the way of the checkout or RSVP.
          </p>
        </div>

        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
            {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : events.length === 0 ? (
          <EmptyState onReset={() => setFilters({ q: '', city: 'All cities', date: 'any', price: 'all' })} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
            {events.map((e, i) => <EventCard key={e.id} event={e} index={i} />)}
          </div>
        )}
      </div>
    </section>
  );
}

function EmptyState({ onReset }) {
  return (
    <div style={{
      border: '1px dashed var(--line-2)', borderRadius: 16,
      padding: '60px 24px', textAlign: 'center',
      background: 'var(--bg-2)',
    }}>
      <div style={{ width: 64, height: 64, margin: '0 auto 18px', opacity: 0.6 }}>
        <StaticMesh scattered={true} accent="rgba(255,255,255,0.6)" width={64} height={64} />
      </div>
      <h3 style={{ margin: 0, fontSize: 17, fontWeight: 500 }}>No events match your filters.</h3>
      <p style={{ margin: '8px 0 20px', color: 'var(--fg-2)', fontSize: 13.5 }}>Try clearing a filter or expanding your date range.</p>
      <button onClick={onReset} style={{
        padding: '10px 16px', borderRadius: 999,
        background: 'transparent', border: '1px solid var(--line-2)',
        color: 'var(--fg)', fontSize: 13,
      }}>Reset filters</button>
    </div>
  );
}
