import { apiClient } from "@/api/client"
import type { CurrentUser } from "@/types"

export async function getCurrentUser(): Promise<CurrentUser> {
  const { data } = await apiClient.get<CurrentUser>("/users/me")
  return data
}

export async function listUsers(): Promise<CurrentUser[]> {
  const { data } = await apiClient.get<CurrentUser[]>("/users")
  return data
}
