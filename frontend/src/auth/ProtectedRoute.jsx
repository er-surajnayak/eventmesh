import { useAuth } from './useAuth';

/**
 * Gates its children on authentication. Reusable for any protected area
 * (account, organizer dashboard, etc.). Renders `fallback` when signed out.
 */
export function ProtectedRoute({ children, fallback = null, loadingFallback = null }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return loadingFallback;
  if (!isAuthenticated) return fallback;
  return children;
}
