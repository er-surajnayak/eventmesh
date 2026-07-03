import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// True only when the required build-time env vars are present.
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

if (!isSupabaseConfigured) {
  console.error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY environment variables.');
}

// Never throw at import time (that white-screens the whole app). When config is
// missing we still construct a client with harmless placeholders so imports
// succeed; the app root renders a config-error screen instead of mounting.
export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-anon-key',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storageKey: 'eventmesh.auth',
    },
  },
);

/**
 * Which auth providers the Supabase project actually has enabled
 * (GoTrue /settings). Lets the UI avoid offering a provider that would fail —
 * e.g. showing "Continue with Google" when Google isn't configured redirects to
 * a 400 "provider is not enabled" error page. Fails safe to {} (email is always
 * on), so a transient settings error hides Google rather than showing it broken.
 */
export async function fetchEnabledProviders() {
  if (!isSupabaseConfigured) return {};
  try {
    const res = await fetch(`${supabaseUrl}/auth/v1/settings`, {
      headers: { apikey: supabaseAnonKey },
    });
    if (!res.ok) return {};
    const data = await res.json();
    return data.external || {};
  } catch {
    return {};
  }
}
