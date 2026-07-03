import { supabase } from './supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetch wrapper for the EventMesh backend. Automatically attaches the current
 * Supabase access token as a Bearer header when the user is signed in.
 */
export async function apiFetch(path, { method = 'GET', body, headers = {}, auth = true, signal } = {}) {
  const finalHeaders = { 'Content-Type': 'application/json', ...headers };

  if (auth) {
    const { data } = await supabase.auth.getSession();
    const token = data?.session?.access_token;
    if (token) finalHeaders.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: finalHeaders,
    body: body != null ? JSON.stringify(body) : undefined,
    signal,
  });

  const isJson = (response.headers.get('content-type') || '').includes('application/json');
  const payload = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    const message = payload?.error?.message || `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    error.body = payload;
    throw error;
  }

  return payload;
}

/** Serialize a params object into a query string, dropping null/undefined/''. */
function toQuery(params = {}) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === '') continue;
    search.append(key, value);
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

export const api = {
  // Public discovery feed (visible read model: native published + canonical imported)
  browseEvents: (params, { signal } = {}) =>
    apiFetch(`/api/v1/events${toQuery(params)}`, { auth: false, signal }),
  getEvent: (slug, { signal } = {}) =>
    apiFetch(`/api/v1/events/${encodeURIComponent(slug)}`, { auth: false, signal }),

  // Profile
  getMe: () => apiFetch('/api/v1/users/me'),
  updateMe: (payload) => apiFetch('/api/v1/users/me', { method: 'PATCH', body: payload }),
  becomeOrganizer: () => apiFetch('/api/v1/users/me/become-organizer', { method: 'POST' }),

  // Organizations
  listOrganizations: () => apiFetch('/api/v1/organizations'),
  getOrganization: (slug) => apiFetch(`/api/v1/organizations/${slug}`, { auth: false }),
  createOrganization: (payload) => apiFetch('/api/v1/organizations', { method: 'POST', body: payload }),

  // Organizer events (org-scoped)
  listOrgEvents: (slug) => apiFetch(`/api/v1/organizations/${slug}/events`),
  getOrgEvent: (slug, id) => apiFetch(`/api/v1/organizations/${slug}/events/${id}`),
  createEvent: (slug, payload) =>
    apiFetch(`/api/v1/organizations/${slug}/events`, { method: 'POST', body: payload }),
  updateEvent: (slug, id, payload) =>
    apiFetch(`/api/v1/organizations/${slug}/events/${id}`, { method: 'PATCH', body: payload }),
  deleteEvent: (slug, id) =>
    apiFetch(`/api/v1/organizations/${slug}/events/${id}`, { method: 'DELETE' }),
  eventAction: (slug, id, action) =>
    apiFetch(`/api/v1/organizations/${slug}/events/${id}/${action}`, { method: 'POST' }),
};
