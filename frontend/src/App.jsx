import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { FilterBar } from './components/FilterBar';
import { EventGridSection } from './components/EventGridSection';
import { HowItWorks } from './components/HowItWorks';
import { SourcesStrip } from './components/SourcesStrip';
import { Footer } from './components/Footer';
import { TweaksPanel } from './components/TweaksPanel';
import { useRevealOnScroll } from './hooks/useRevealOnScroll';

const TWEAK_DEFAULTS = {
  accent: "#FFB84D",
  meshIntensity: 1,
  meshDensity: 1.1
};

function App() {
  const [filters, setFilters] = useState({
    q: '', city: 'San Francisco', date: 'all', price: 'all', type: 'all'
  });
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
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

  // Fetch events from backend
  useEffect(() => {
    async function fetchEvents() {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.city) params.append('city', filters.city);
        if (filters.price !== 'all') params.append('free', filters.price === 'free');
        if (filters.type !== 'all') params.append('online', filters.type === 'online');
        if (filters.date !== 'all') params.append('date_range', filters.date);
        if (filters.q) params.append('search', filters.q);

        const isProd = window.location.hostname !== 'localhost';
        const baseUrl = isProd ? 'https://eventmesh-b.vercel.app' : 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/events/?${params.toString()}`);
        const data = await response.json();
        setEvents(data.events || []);
      } catch (error) {
        console.error("Failed to fetch events:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchEvents();
  }, [filters]);

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

  return (
    <>
      <Navbar onExplore={explore} />
      <Hero onExplore={explore} tweaks={tweaks} />
      <FilterBar filters={filters} setFilters={setFilters} resultCount={events.length} />
      <EventGridSection filters={filters} setFilters={setFilters} events={events} loading={loading} />
      <HowItWorks tweaks={tweaks} />
      <SourcesStrip tweaks={tweaks} />
      <Footer />
      <TweaksPanel tweaks={tweaks} setTweaks={setTweaks} visible={tweakMode} />
    </>
  );
}

export default App;
