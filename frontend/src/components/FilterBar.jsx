import React, { useState, useEffect, useRef } from 'react';
import { Icon } from './UIPrimitives';
import { DATE_FILTERS, PRICE_FILTERS, TYPE_FILTERS, DEFAULT_FILTERS } from '../data/events';
import { SOURCE_OPTIONS } from '../utils/adaptEvent';
import { CitySelect } from './CitySelect';

const SourceIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

export function FilterBar({ filters, setFilters, resultCount }) {
  const setK = (k, v) => setFilters(f => ({ ...f, [k]: v }));

  const isFiltered = Object.keys(DEFAULT_FILTERS).some((k) => filters[k] !== DEFAULT_FILTERS[k]);

  return (
    <div id="discover" style={{
      position: 'sticky', top: 64, zIndex: 30,
      background: 'var(--glass-2)',
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
          <span style={{ color: 'var(--fg-3)' }} aria-hidden="true">{Icon.search}</span>
          <input
            type="search"
            value={filters.q}
            onChange={e => setK('q', e.target.value)}
            placeholder="Search talks, yoga, house music…"
            aria-label="Search events"
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: 'var(--fg)', fontFamily: 'inherit', fontSize: 13.5,
            }}
          />
          {filters.q && (
            <button onClick={() => setK('q', '')} aria-label="Clear search" style={{
              background: 'none', border: 'none', color: 'var(--fg-3)', padding: 2, display: 'grid', placeItems: 'center',
            }}>{Icon.x}</button>
          )}
        </div>

        <CitySelect value={filters.city} onChange={v => setK('city', v)} />

        <SelectFilter
          value={filters.source}
          onChange={v => setK('source', v)}
          options={SOURCE_OPTIONS}
          icon={SourceIcon}
        />

        <SegmentedFilter
          value={filters.date}
          onChange={v => setK('date', v)}
          options={DATE_FILTERS}
          label="Filter by date"
        />

        <SegmentedFilter
          value={filters.type}
          onChange={v => setK('type', v)}
          options={TYPE_FILTERS}
          label="Filter by format"
        />

        <SegmentedFilter
          value={filters.price}
          onChange={v => setK('price', v)}
          options={PRICE_FILTERS}
          label="Filter by price"
        />

        <div style={{ flex: 1 }} />

        {isFiltered && (
          <button
            onClick={() => setFilters(DEFAULT_FILTERS)}
            className="mono"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
              color: 'var(--fg-2)', background: 'transparent',
              border: '1px solid var(--line-2)', borderRadius: 999, padding: '6px 12px',
            }}
          >
            {Icon.x} Clear
          </button>
        )}

        <div
          className="mono"
          role="status"
          aria-live="polite"
          style={{ fontSize: 11.5, color: 'var(--fg-3)', letterSpacing: '0.08em', textTransform: 'uppercase' }}
        >
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
      <button
        onClick={() => setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`Filter: ${value}`}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '10px 14px', borderRadius: 10,
          background: 'var(--bg-2)', border: '1px solid var(--line-2)',
          color: 'var(--fg)', fontSize: 13,
          transition: 'border-color 0.15s',
        }}
      >
        <span style={{ color: 'var(--fg-3)' }} aria-hidden="true">{icon}</span>
        <span>{value}</span>
        <span style={{ color: 'var(--fg-3)', marginLeft: 4, transform: open ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }} aria-hidden="true">{Icon.chevron}</span>
      </button>
      {open && (
        <div role="listbox" style={{
          position: 'absolute', top: 'calc(100% + 6px)', left: 0, minWidth: 200,
          background: 'var(--bg-2)', border: '1px solid var(--line-2)', borderRadius: 10,
          padding: 6, zIndex: 20,
          boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
        }}>
          {options.map(opt => (
            <button key={opt} role="option" aria-selected={opt === value} onClick={() => { onChange(opt); setOpen(false); }} style={{
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

function SegmentedFilter({ value, onChange, options, label }) {
  return (
    <div
      role="group"
      aria-label={label}
      style={{
        display: 'inline-flex', padding: 3, borderRadius: 10,
        background: 'var(--bg-2)', border: '1px solid var(--line-2)',
      }}
    >
      {options.map(opt => {
        const active = opt.key === value;
        return (
          <button key={opt.key} onClick={() => onChange(opt.key)} aria-pressed={active} style={{
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
