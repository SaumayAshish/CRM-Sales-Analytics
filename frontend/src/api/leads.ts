import { apiClient } from "@/api/client"
import type { Activity, Lead } from "@/types"

export interface LeadFilters {
  status_unassigned?: boolean
  source_id?: string
  assigned_to?: string
  page?: number
  page_size?: number
}

export interface LeadCreatePayload {
  first_name: string
  last_name: string
  company: string
  email: string
  phone?: string
  source_id: string
}

export type LeadUpdatePayload = Partial<LeadCreatePayload>

export interface LeadConvertResponse {
  account_id: string
  contact_id: string
  opportunity_id: string
}

export async function listLeads(filters: LeadFilters = {}): Promise<Lead[]> {
  const { data } = await apiClient.get<Lead[]>("/leads", { params: filters })
  return data
}

export async function getLead(id: string): Promise<Lead> {
  const { data } = await apiClient.get<Lead>(`/leads/${id}`)
  return data
}

export async function createLead(payload: LeadCreatePayload): Promise<Lead> {
  const { data } = await apiClient.post<Lead>("/leads", payload)
  return data
}

export async function updateLead(id: string, payload: LeadUpdatePayload): Promise<Lead> {
  const { data } = await apiClient.patch<Lead>(`/leads/${id}`, payload)
  return data
}

export async function deleteLead(id: string): Promise<void> {
  await apiClient.delete(`/leads/${id}`)
}

export async function assignLead(id: string, assignedTo: string): Promise<Lead> {
  const { data } = await apiClient.post<Lead>(`/leads/${id}/assign`, { assigned_to: assignedTo })
  return data
}

export async function convertLead(id: string): Promise<LeadConvertResponse> {
  const { data } = await apiClient.post<LeadConvertResponse>(`/leads/${id}/convert`)
  return data
}

export async function getLeadTimeline(id: string): Promise<Activity[]> {
  const { data } = await apiClient.get<Activity[]>(`/leads/${id}/timeline`)
  return data
}

export interface ScoreBreakdown {
  lead_id: string
  score: number
  score_band: string
  scoring_rule_id: string | null
  matched_criteria: Array<{
    field_name: string
    operator: string
    comparison_value: string
    weight: number
  }>
}

export async function getScoreBreakdown(id: string): Promise<ScoreBreakdown> {
  const { data } = await apiClient.get<ScoreBreakdown>(`/leads/${id}/score-breakdown`)
  return data
}
