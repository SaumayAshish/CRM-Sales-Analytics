import { apiClient } from "@/api/client"
import type { Notification } from "@/types"

export async function listNotifications(): Promise<Notification[]> {
  const { data } = await apiClient.get<Notification[]>("/notifications")
  return data
}

export async function markNotificationRead(id: string): Promise<Notification> {
  const { data } = await apiClient.patch<Notification>(`/notifications/${id}/mark-read`)
  return data
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.post("/notifications/mark-all-read")
}
