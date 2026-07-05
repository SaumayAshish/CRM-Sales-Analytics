import { apiClient } from "@/api/client"
import type { Opportunity } from "@/types"

export interface OpportunityFilters {
  stage_id?: string
  owner_id?: string
  close_date_from?: string
  close_date_to?: string
  page?: number
  page_size?: number
}

export interface OpportunityCreatePayload {
  name: string
  account_id: string
  owner_id: string
  stage_id: string
  amount: number
  probability: number
  expected_close_date: string
}

export type OpportunityUpdatePayload = Partial<
  Pick<OpportunityCreatePayload, "name" | "owner_id" | "amount" | "probability" | "expected_close_date">
>

export interface StageChangePayload {
  stage_id: string
  loss_reason_id?: string
  override_reason?: string
}

export interface StageHistoryEntry {
  id: string
  actor_id: string | null
  before_state: Record<string, unknown> | null
  after_state: Record<string, unknown> | null
  created_at: string
}

export async function listOpportunities(filters: OpportunityFilters = {}): Promise<Opportunity[]> {
  const { data } = await apiClient.get<Opportunity[]>("/opportunities", { params: filters })
  return data
}

export async function getOpportunity(id: string): Promise<Opportunity> {
  const { data } = await apiClient.get<Opportunity>(`/opportunities/${id}`)
  return data
}

export async function createOpportunity(payload: OpportunityCreatePayload): Promise<Opportunity> {
  const { data } = await apiClient.post<Opportunity>("/opportunities", payload)
  return data
}

export async function updateOpportunity(id: string, payload: OpportunityUpdatePayload): Promise<Opportunity> {
  const { data } = await apiClient.patch<Opportunity>(`/opportunities/${id}`, payload)
  return data
}

export async function deleteOpportunity(id: string): Promise<void> {
  await apiClient.delete(`/opportunities/${id}`)
}

export async function advanceStage(id: string, payload: StageChangePayload): Promise<Opportunity> {
  const { data } = await apiClient.post<Opportunity>(`/opportunities/${id}/advance-stage`, payload)
  return data
}

export async function getStageHistory(id: string): Promise<StageHistoryEntry[]> {
  const { data } = await apiClient.get<StageHistoryEntry[]>(`/opportunities/${id}/stage-history`)
  return data
}
