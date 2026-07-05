// Client-side role gating. Traces to: FR-45 (UI gating only -- the
// backend's require_role dependency is the actual enforcement, per
// FR-39; this component must never be the only check for a sensitive
// action).
import type { ReactNode } from "react"

import { useAuth } from "@/hooks/useAuth"
import type { Role } from "@/types"

interface RoleGuardProps {
  allow: Role[]
  children: ReactNode
  fallback?: ReactNode
}

export function RoleGuard({ allow, children, fallback = null }: RoleGuardProps) {
  const { role } = useAuth()
  if (!role || !allow.includes(role)) {
    return <>{fallback}</>
  }
  return <>{children}</>
}
