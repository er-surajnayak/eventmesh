import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { FilterBar } from './components/FilterBar';
import { EventGridSection } from './components/EventGridSection';
import { HowItWorks } from './components/HowItWorks';
import { SourcesStrip } from './components/SourcesStrip';
import { Footer } from './components/Footer';
import { TweaksPanel } from './components/TweaksPanel';
import { useRevealOnScroll } from './hooks/useRevealOnScroll';
import { filterEvents } from './utils/filters';
import { EVENTS } from './data/events';

const TWEAK_DEFAULTS = {
  accent: "#FFB84D",
  meshIntensity: 1,
  meshDensity: 1.1
};

function App() {
  const [filters, setFilters] = useState({
    q: '', city: 'All cities', date: 'any', price: 'all',
  });
  const [tweaks, setTweaks] = useState(TWEAK_DEFAULTS);
  const [tweakMode, setTweakMode] = useState(false);

  // Apply accent to CSS variables
  useEffect(() => {
    document.documentElement.style.setProperty('--accent', tweaks.accent);
    const m = tweaks.accent.replace('#',''); 
    const n = parseInt(m, 16);
    const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    document.documentElement.style.setProperty('--accent-glow', `rgba(${r},${g},${b},0.35)`);
  }, [tweaks.accent]);

  // Activate edit mode or other protocols if needed
  useEffect(() => {
    function onMsg(e) {
      const d = e.data;
      if (!d || typeof d !== 'object') return;
      if (d.type === '__activate_edit_mode') setTweakMode(true);
      if (d.type === '__deactivate_edit_mode') setTweakMode(false);
    }
    window.addEventListener('message', onMsg);
    if (window.parent !== window) {
      window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    }
    return () => window.removeEventListener('message', onMsg);
  }, []);

  useRevealOnScroll();

  const explore = useCallback(() => {
    const el = document.getElementById('discover');
    if (el) {
      const top = el.getBoundingClientRect().top + window.scrollY - 60;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  }, []);

  const resultsLength = useMemo(() => filterEvents(EVENTS, filters).length, [filters]);

  return (
    <>
      <Navbar onExplore={explore} />
      <Hero onExplore={explore} tweaks={tweaks} />
      <FilterBar filters={filters} setFilters={setFilters} resultCount={resultsLength} />
      <EventGridSection filters={filters} setFilters={setFilters} />
      <HowItWorks tweaks={tweaks} />
      <SourcesStrip tweaks={tweaks} />
      <Footer />
      <TweaksPanel tweaks={tweaks} setTweaks={setTweaks} visible={tweakMode} />
    </>
  );
}

export default App;
