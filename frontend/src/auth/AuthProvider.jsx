import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { supabase, fetchEnabledProviders } from '../lib/supabaseClient';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState(null);

  useEffect(() => {
    let mounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      setSession(data.session);
      setLoading(false);
    });

    fetchEnabledProviders().then((ext) => {
      if (mounted) setProviders(ext);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });

    return () => {
      mounted = false;
      sub.subscription.unsubscribe();
    };
  }, []);

  const signInWithOtp = useCallback(
    (email) => supabase.auth.signInWithOtp({ email, options: { shouldCreateUser: true } }),
    [],
  );
  const verifyOtp = useCallback(
    (email, token) => supabase.auth.verifyOtp({ email, token, type: 'email' }),
    [],
  );
  const signInWithGoogle = useCallback(
    () =>
      supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: window.location.origin },
      }),
    [],
  );
  const signOut = useCallback(() => supabase.auth.signOut(), []);

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      isAuthenticated: Boolean(session),
      loading,
      // Only true once /settings confirms Google is enabled; null while unknown.
      googleEnabled: providers?.google === true,
      signInWithOtp,
      verifyOtp,
      signInWithGoogle,
      signOut,
    }),
    [session, loading, providers, signInWithOtp, verifyOtp, signInWithGoogle, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
