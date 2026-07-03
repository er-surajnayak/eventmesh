import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import App from './App.jsx'
import { AuthProvider } from './auth/AuthProvider'
import { ProfileProvider } from './profile/ProfileProvider'
import { OrganizerApp } from './organizer/OrganizerApp'
import { EventDetail } from './events/EventDetail'
import { ConfigError } from './ConfigError.jsx'
import { isSupabaseConfigured } from './lib/supabaseClient'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isSupabaseConfigured ? (
      <BrowserRouter>
        <AuthProvider>
          <ProfileProvider>
            <Routes>
              <Route path="/" element={<App />} />
              <Route path="/events/:slug" element={<EventDetail />} />
              <Route path="/organizer/*" element={<OrganizerApp />} />
            </Routes>
          </ProfileProvider>
        </AuthProvider>
      </BrowserRouter>
    ) : (
      <ConfigError />
    )}
  </React.StrictMode>,
)
