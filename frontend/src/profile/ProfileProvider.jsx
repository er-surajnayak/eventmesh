import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../auth/useAuth';
import { api } from '../lib/apiClient';

export const ProfileContext = createContext(null);

/**
 * Owns the authenticated user's application profile — deliberately separate from
 * AuthProvider (which owns only session/token state). Loads /users/me when the
 * user is authenticated, and clears it on sign-out.
 */
export function ProfileProvider({ children }) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMe();
      setProfile(data);
      return data;
    } catch (err) {
      setError(err);
      setProfile(null);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated) {
      refresh().catch(() => {});
    } else {
      setProfile(null);
      setError(null);
    }
  }, [isAuthenticated, authLoading, refresh]);

  const updateProfile = useCallback(async (payload) => {
    const updated = await api.updateMe(payload);
    setProfile(updated);
    return updated;
  }, []);

  const becomeOrganizer = useCallback(async () => {
    const updated = await api.becomeOrganizer();
    setProfile(updated);
    return updated;
  }, []);

  const value = useMemo(
    () => ({ profile, loading, error, refresh, updateProfile, becomeOrganizer }),
    [profile, loading, error, refresh, updateProfile, becomeOrganizer],
  );

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}
