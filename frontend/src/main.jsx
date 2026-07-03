import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import App from './App.jsx'
import { AuthProvider } from './auth/AuthProvider'
import { ProfileProvider } from './profile/ProfileProvider'
import { ConfigError } from './ConfigError.jsx'
import { isSupabaseConfigured } from './lib/supabaseClient'
import './index.css'

// Code-split the heavy, non-landing routes so the discovery page ships a lean
// initial bundle; they load on demand.
const OrganizerApp = lazy(() =>
  import('./organizer/OrganizerApp').then((m) => ({ default: m.OrganizerApp })),
)
const EventDetail = lazy(() =>
  import('./events/EventDetail').then((m) => ({ default: m.EventDetail })),
)

function RouteFallback() {
  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', color: 'var(--fg-3)' }}>
      Loading…
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isSupabaseConfigured ? (
      <BrowserRouter>
        <AuthProvider>
          <ProfileProvider>
            <Suspense fallback={<RouteFallback />}>
              <Routes>
                <Route path="/" element={<App />} />
                <Route path="/events/:slug" element={<EventDetail />} />
                <Route path="/organizer/*" element={<OrganizerApp />} />
              </Routes>
            </Suspense>
          </ProfileProvider>
        </AuthProvider>
      </BrowserRouter>
    ) : (
      <ConfigError />
    )}
  </React.StrictMode>,
)
