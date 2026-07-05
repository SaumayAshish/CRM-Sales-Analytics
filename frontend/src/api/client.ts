// Axios instance with a JWT interceptor and refresh-on-401 handling.
// Traces to: FR-38, FR-43 (access + refresh token pair, ADR-003).
import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios"

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth-storage"

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
})

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  try {
    const response = await axios.post(
      `${apiClient.defaults.baseURL}/auth/refresh`,
      { refresh_token: refreshToken }
    )
    const newAccessToken = response.data.access_token as string
    setTokens(newAccessToken)
    return newAccessToken
  } catch {
    clearTokens()
    return null
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true

      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })
      const newToken = await refreshPromise

      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return apiClient(originalRequest)
      }

      clearTokens()
      window.location.href = "/login"
    }

    return Promise.reject(error)
  }
)
