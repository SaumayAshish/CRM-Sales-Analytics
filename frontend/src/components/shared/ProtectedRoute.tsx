// Redirects to /login when unauthenticated; auto-logout on token expiry
// is implicitly handled since useAuth() decodes and checks exp on load,
// and the Axios interceptor (api/client.ts) redirects on a 401 refresh failure.
import { Navigate, Outlet } from "react-router-dom"

import { useAuth } from "@/hooks/useAuth"

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center text-muted-foreground">Loading…</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
