import { apiClient } from "@/api/client"
import type { Activity } from "@/types"

export interface ActivityFilters {
  lead_id?: string
  account_id?: string
  opportunity_id?: string
  page?: number
  page_size?: number
}

export interface ActivityCreatePayload {
  type_id: string
  lead_id?: string
  account_id?: string
  contact_id?: string
  opportunity_id?: string
  notes?: string
  due_at?: string
}

export interface ActivityUpdatePayload {
  notes?: string
  is_complete?: boolean
  due_at?: string
}

export async function listActivities(filters: ActivityFilters = {}): Promise<Activity[]> {
  const { data } = await apiClient.get<Activity[]>("/activities", { params: filters })
  return data
}

export async function createActivity(payload: ActivityCreatePayload): Promise<Activity> {
  const { data } = await apiClient.post<Activity>("/activities", payload)
  return data
}

export async function updateActivity(id: string, payload: ActivityUpdatePayload): Promise<Activity> {
  const { data } = await apiClient.patch<Activity>(`/activities/${id}`, payload)
  return data
}

export async function deleteActivity(id: string): Promise<void> {
  await apiClient.delete(`/activities/${id}`)
}
