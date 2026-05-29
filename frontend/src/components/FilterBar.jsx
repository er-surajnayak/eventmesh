import React, { useState, useEffect, useRef } from 'react';
import { Icon } from './UIPrimitives';
import { CITIES, DATE_FILTERS, PRICE_FILTERS, TYPE_FILTERS } from '../data/events';

export function FilterBar({ filters, setFilters, resultCount }) {
  const setK = (k, v) => setFilters(f => ({ ...f, [k]: v }));
  const [detectedCity, setDetectedCity] = useState(null);

  useEffect(() => {
    // Basic city detection based on geolocation (simulated or real)
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        // In a real app, you'd reverse geocode here. 
        // For now, we'll suggest a city if they're near one.
        setDetectedCity('San Francisco'); // Mocking detection for now
      });
    }
  }, []);

  const sortedCities = [...CITIES].sort((a, b) => {
    if (a === detectedCity) return -1;
    if (b === detectedCity) return 1;
    return 0;
  });

  return (
    <div id="discover" style={{
      position: 'sticky', top: 64, zIndex: 30,
      background: 'rgba(5,5,5,0.82)',
      backdropFilter: 'blur(14px) saturate(1.2)',
      WebkitBackdropFilter: 'blur(14px) saturate(1.2)',
      borderBottom: '1px solid var(--line)',
    }}>
      <div className="container" style={{ padding: '18px 32px', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{
          flex: '1 1 320px', minWidth: 240, display: 'flex', alignItems: 'center', gap: 10,
          padding: '10px 14px', border: '1px solid var(--line-2)', borderRadius: 10,
          background: 'var(--bg-2)',
          transition: 'border-color 0.2s',
        }}>
          <span style={{ color: 'var(--fg-3)' }}>{Icon.search}</span>
          <input
            value={filters.q}
            onChange={e => setK('q', e.target.value)}
            placeholder="Search talks, yoga, house music…"
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: 'var(--fg)', fontFamily: 'inherit', fontSize: 13.5,
            }}
          />
          {filters.q && (
            <button onClick={() => setK('q', '')} style={{
              background: 'none', border: 'none', color: 'var(--fg-3)', padding: 2, display: 'grid', placeItems: 'center',
            }}>{Icon.x}</button>
          )}
        </div>

        <SelectFilter
          value={filters.city}
          onChange={v => setK('city', v)}
          options={sortedCities}
          icon={Icon.pin}
          recommendation={detectedCity}
        />

        <SegmentedFilter
          value={filters.date}
          onChange={v => setK('date', v)}
          options={DATE_FILTERS}
        />

        <SegmentedFilter
          value={filters.type}
          onChange={v => setK('type', v)}
          options={TYPE_FILTERS}
        />

        <SegmentedFilter
          value={filters.price}
          onChange={v => setK('price', v)}
          options={PRICE_FILTERS}
        />

        <div style={{ flex: 1 }} />

        <div className="mono" style={{ fontSize: 11.5, color: 'var(--fg-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          {resultCount} {resultCount === 1 ? 'result' : 'results'}
        </div>
      </div>
    </div>
  );
}

function SelectFilter({ value, onChange, options, icon, recommendation }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    window.addEventListener('mousedown', h);
    return () => window.removeEventListener('mousedown', h);
  }, []);
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button onClick={() => setOpen(o => !o)} style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 14px', borderRadius: 10,
        background: 'var(--bg-2)', border: '1px solid var(--line-2)',
        color: 'var(--fg)', fontSize: 13,
        transition: 'border-color 0.15s',
      }}>
        <span style={{ color: 'var(--fg-3)' }}>{icon}</span>
        <span>{value}</span>
        <span style={{ color: 'var(--fg-3)', marginLeft: 4, transform: open ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }}>{Icon.chevron}</span>
      </button>
      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 6px)', left: 0, minWidth: 200,
          background: 'var(--bg-2)', border: '1px solid var(--line-2)', borderRadius: 10,
          padding: 6, zIndex: 20,
          boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
        }}>
          {options.map(opt => (
            <button key={opt} onClick={() => { onChange(opt); setOpen(false); }} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              width: '100%', textAlign: 'left',
              padding: '8px 10px', borderRadius: 6,
              background: opt === value ? 'rgba(0,214,255,0.08)' : 'transparent',
              color: opt === value ? 'var(--accent)' : 'var(--fg)',
              border: 'none', fontSize: 13,
              transition: 'background 0.15s',
              cursor: 'pointer',
            }}>
              <span>{opt}</span>
              {opt === recommendation && (
                <span className="mono" style={{ fontSize: 9, color: 'var(--accent)', opacity: 0.8 }}>RECOMMENDED</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SegmentedFilter({ value, onChange, options }) {
  return (
    <div style={{
      display: 'inline-flex', padding: 3, borderRadius: 10,
      background: 'var(--bg-2)', border: '1px solid var(--line-2)',
    }}>
      {options.map(opt => {
        const active = opt.key === value;
        return (
          <button key={opt.key} onClick={() => onChange(opt.key)} style={{
            padding: '7px 12px', borderRadius: 7, border: 'none',
            background: active ? 'rgba(0,214,255,0.1)' : 'transparent',
            color: active ? 'var(--accent)' : 'var(--fg-2)',
            fontSize: 12.5, fontWeight: active ? 500 : 400,
            transition: 'all 0.2s',
          }}>{opt.label}</button>
        );
      })}
    </div>
  );
}
