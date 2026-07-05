// localStorage-based token storage, per the Phase 4 kickoff decision
// (localStorage + Axios interceptor -- matches the existing backend
// contract from ADR-003 with zero backend rework).

const ACCESS_TOKEN_KEY = "crm_access_token"
const REFRESH_TOKEN_KEY = "crm_refresh_token"

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken: string, refreshToken?: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  }
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}
