import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Icon } from './UIPrimitives';
import {
  ALL_CITIES,
  RECOMMENDED_CITIES,
  MAJOR_INDIAN_CITIES,
  INTERNATIONAL_CITIES,
  nearestSupportedCity,
} from '../data/cities';

const CITY_KEY = 'eventmesh.city';
const DETECTED_KEY = 'eventmesh.detectedCity';

function readStored(key) {
  try {
    return localStorage.getItem(key) || null;
  } catch {
    return null;
  }
}
function writeStored(key, value) {
  try {
    if (value) localStorage.setItem(key, value);
  } catch {
    /* storage unavailable — selection just won't persist */
  }
}

const LocationIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3.5" />
    <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
  </svg>
);

const Check = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 6 9 17l-5-5" />
  </svg>
);

// India-first city selector. Geolocation is requested only when the user clicks
// "Use my location"; the pick persists to localStorage. Keeps the existing
// dropdown look — this only improves ordering, grouping, and a11y.
export function CitySelect({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const [detected, setDetected] = useState(() => readStored(DETECTED_KEY));
  const [locating, setLocating] = useState(false);
  const [locateError, setLocateError] = useState('');

  const rootRef = useRef(null);
  const panelRef = useRef(null);
  const triggerRef = useRef(null);
  // Captured at first render so the persist effect can't clobber it before hydrate.
  const storedCity = useRef(readStored(CITY_KEY));

  const select = (city) => {
    onChange(city);
    setOpen(false);
    triggerRef.current?.focus();
  };

  // Hydrate the previously selected city on first mount — but only when the URL
  // didn't already set one (value still the default) so shared links win.
  useEffect(() => {
    if (value === ALL_CITIES && storedCity.current && storedCity.current !== ALL_CITIES) {
      onChange(storedCity.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist every city change (so returning visitors land on their last city).
  useEffect(() => {
    if (value) writeStored(CITY_KEY, value);
  }, [value]);

  // Close on outside click.
  useEffect(() => {
    const onDown = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    window.addEventListener('mousedown', onDown);
    return () => window.removeEventListener('mousedown', onDown);
  }, []);

  // On open, move focus into the list (selected item, else first item).
  useLayoutEffect(() => {
    if (!open || !panelRef.current) return;
    const items = panelRef.current.querySelectorAll('[data-cityitem]');
    const selected = panelRef.current.querySelector('[aria-selected="true"]');
    (selected || items[0])?.focus();
  }, [open]);

  const useMyLocation = () => {
    setLocateError('');
    if (!('geolocation' in navigator)) {
      setLocateError('Location isn’t available on this device.');
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        const city = nearestSupportedCity(pos.coords.latitude, pos.coords.longitude);
        if (city) {
          setDetected(city);
          writeStored(DETECTED_KEY, city);
          select(city);
        } else {
          select('Mumbai');
        }
      },
      () => {
        // Denied or failed → sensible India-first fallback.
        setLocating(false);
        setLocateError('Location unavailable — showing Mumbai.');
        select('Mumbai');
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 600000 },
    );
  };

  // Recommended = detected (if any) + Mumbai + Bangalore, de-duplicated. The
  // detected city is lifted here and removed from the groups below.
  const recommended = [...new Set([detected, ...RECOMMENDED_CITIES].filter(Boolean))];
  const major = MAJOR_INDIAN_CITIES.filter((c) => c !== detected);
  const international = INTERNATIONAL_CITIES.filter((c) => c !== detected);

  const onPanelKeyDown = (e) => {
    const items = [...panelRef.current.querySelectorAll('[data-cityitem]')];
    if (!items.length) return;
    const idx = items.indexOf(document.activeElement);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      items[idx < 0 ? 0 : Math.min(idx + 1, items.length - 1)].focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      items[idx <= 0 ? 0 : idx - 1].focus();
    } else if (e.key === 'Home') {
      e.preventDefault();
      items[0].focus();
    } else if (e.key === 'End') {
      e.preventDefault();
      items[items.length - 1].focus();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setOpen(false);
      triggerRef.current?.focus();
    } else if (e.key.length === 1 && /[a-z]/i.test(e.key)) {
      // Type-ahead: jump to the next city starting with the typed letter.
      const start = idx < 0 ? 0 : idx + 1;
      const ordered = [...items.slice(start), ...items.slice(0, start)];
      const match = ordered.find((el) => el.dataset.cityname?.toLowerCase().startsWith(e.key.toLowerCase()));
      match?.focus();
    }
  };

  const optionStyle = (city) => ({
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    width: '100%', textAlign: 'left', gap: 10,
    padding: '8px 10px', borderRadius: 6,
    background: city === value ? 'rgba(0,214,255,0.08)' : 'transparent',
    color: city === value ? 'var(--accent)' : 'var(--fg)',
    border: 'none', fontSize: 13, cursor: 'pointer',
  });

  const CityOption = (city) => (
    <button
      key={city}
      role="option"
      aria-selected={city === value}
      data-cityitem
      data-cityname={city}
      tabIndex={-1}
      onClick={() => select(city)}
      style={optionStyle(city)}
    >
      <span>{city}</span>
      {city === value && <span style={{ color: 'var(--accent)' }}>{Check}</span>}
    </button>
  );

  const Header = ({ children }) => (
    <div
      className="mono"
      aria-hidden="true"
      style={{
        fontSize: 9.5, letterSpacing: '0.12em', textTransform: 'uppercase',
        color: 'var(--fg-3)', padding: '8px 10px 4px',
      }}
    >
      {children}
    </div>
  );

  const Divider = () => (
    <div role="separator" style={{ height: 1, background: 'var(--line)', margin: '6px 4px' }} />
  );

  return (
    <div ref={rootRef} style={{ position: 'relative' }}>
      <button
        ref={triggerRef}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (!open && (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            setOpen(true);
          }
        }}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`City: ${value}`}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '10px 14px', borderRadius: 10,
          background: 'var(--bg-2)', border: '1px solid var(--line-2)',
          color: 'var(--fg)', fontSize: 13,
          transition: 'border-color 0.15s',
        }}
      >
        <span style={{ color: 'var(--fg-3)' }} aria-hidden="true">{Icon.pin}</span>
        <span>{value}</span>
        <span
          aria-hidden="true"
          style={{ color: 'var(--fg-3)', marginLeft: 4, transform: open ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }}
        >
          {Icon.chevron}
        </span>
      </button>

      {open && (
        <div
          ref={panelRef}
          role="listbox"
          aria-label="Select a city"
          onKeyDown={onPanelKeyDown}
          style={{
            position: 'absolute', top: 'calc(100% + 6px)', left: 0, minWidth: 240,
            maxHeight: '60vh', overflowY: 'auto',
            background: 'var(--bg-2)', border: '1px solid var(--line-2)', borderRadius: 10,
            padding: 6, zIndex: 40,
            boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
          }}
        >
          <button
            data-cityitem
            data-cityname="use my location"
            tabIndex={-1}
            onClick={useMyLocation}
            aria-label="Use my location to find the nearest city"
            style={{
              display: 'flex', alignItems: 'center', gap: 8, width: '100%',
              padding: '9px 10px', borderRadius: 6, border: '1px solid var(--line-2)',
              background: 'transparent', color: 'var(--accent)', fontSize: 13, cursor: 'pointer',
            }}
          >
            <span aria-hidden="true">{LocationIcon}</span>
            <span>{locating ? 'Detecting your location…' : 'Use my location'}</span>
          </button>
          {locateError && (
            <div role="alert" style={{ fontSize: 11.5, color: 'var(--fg-3)', padding: '6px 10px 2px' }}>
              {locateError}
            </div>
          )}

          <div role="group" aria-label="Recommended cities">
            <Header>Recommended</Header>
            {recommended.map(CityOption)}
          </div>

          <div role="group" aria-label="Major Indian cities">
            <Header>Major Indian Cities</Header>
            {major.map(CityOption)}
          </div>

          <Divider />
          <div role="group" aria-label="All cities">{CityOption(ALL_CITIES)}</div>
          <Divider />

          <div role="group" aria-label="International cities">
            <Header>International Cities</Header>
            {international.map(CityOption)}
          </div>
        </div>
      )}
    </div>
  );
}
