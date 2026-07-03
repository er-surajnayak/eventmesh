import { supabase } from './supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetch wrapper for the EventMesh backend. Automatically attaches the current
 * Supabase access token as a Bearer header when the user is signed in.
 */
export async function apiFetch(path, { method = 'GET', body, headers = {}, auth = true } = {}) {
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

export const api = {
  // Profile
  getMe: () => apiFetch('/api/v1/users/me'),
  updateMe: (payload) => apiFetch('/api/v1/users/me', { method: 'PATCH', body: payload }),
  becomeOrganizer: () => apiFetch('/api/v1/users/me/become-organizer', { method: 'POST' }),

  // Organizations
  listOrganizations: () => apiFetch('/api/v1/organizations'),
  getOrganization: (slug) => apiFetch(`/api/v1/organizations/${slug}`, { auth: false }),
  createOrganization: (payload) => apiFetch('/api/v1/organizations', { method: 'POST', body: payload }),
};
