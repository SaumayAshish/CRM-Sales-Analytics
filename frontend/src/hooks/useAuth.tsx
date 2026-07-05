// Auth context: login/logout, decoded role claim, current-user profile.
// Traces to: FR-38 (JWT with role claim), FR-45 (profile for UI gating).
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { jwtDecode } from "jwt-decode"

import { login as loginRequest, logout as logoutRequest } from "@/api/auth"
import { getCurrentUser } from "@/api/users"
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth-storage"
import type { CurrentUser, Role } from "@/types"

interface JwtClaims {
  sub: string
  role: Role
  exp: number
}

interface AuthContextValue {
  isAuthenticated: boolean
  role: Role | null
  user: CurrentUser | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function decodeRole(token: string): Role | null {
  try {
    const claims = jwtDecode<JwtClaims>(token)
    if (claims.exp * 1000 < Date.now()) return null
    return claims.role
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role | null>(null)
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    const decodedRole = decodeRole(token)
    if (!decodedRole) {
      clearTokens()
      setIsLoading(false)
      return
    }
    setRole(decodedRole)
    getCurrentUser()
      .then(setUser)
      .catch(() => {
        clearTokens()
        setRole(null)
      })
      .finally(() => setIsLoading(false))
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: role !== null,
      role,
      user,
      isLoading,
      async login(email: string, password: string) {
        const tokens = await loginRequest({ email, password })
        setTokens(tokens.access_token, tokens.refresh_token)
        const decodedRole = decodeRole(tokens.access_token)
        setRole(decodedRole)
        const profile = await getCurrentUser()
        setUser(profile)
      },
      async logout() {
        const refreshToken = getRefreshToken()
        if (refreshToken) {
          await logoutRequest(refreshToken).catch(() => undefined)
        }
        clearTokens()
        setRole(null)
        setUser(null)
      },
    }),
    [role, user, isLoading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider")
  return ctx
}
