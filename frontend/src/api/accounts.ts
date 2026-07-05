import { apiClient } from "@/api/client"
import type { Account, Activity, Contact, Opportunity } from "@/types"

export interface AccountFilters {
  name?: string
  owner_id?: string
  page?: number
  page_size?: number
}

export interface AccountCreatePayload {
  name: string
  domain?: string
  industry?: string
  owner_id: string
  override_duplicate_warning?: boolean
  override_reason?: string
}

export type AccountUpdatePayload = Partial<Omit<AccountCreatePayload, "override_duplicate_warning" | "override_reason">>

export async function listAccounts(filters: AccountFilters = {}): Promise<Account[]> {
  const { data } = await apiClient.get<Account[]>("/accounts", { params: filters })
  return data
}

export async function getAccount(id: string): Promise<Account> {
  const { data } = await apiClient.get<Account>(`/accounts/${id}`)
  return data
}

export async function createAccount(payload: AccountCreatePayload): Promise<Account> {
  const { data } = await apiClient.post<Account>("/accounts", payload)
  return data
}

export async function updateAccount(id: string, payload: AccountUpdatePayload): Promise<Account> {
  const { data } = await apiClient.patch<Account>(`/accounts/${id}`, payload)
  return data
}

export async function deleteAccount(id: string): Promise<void> {
  await apiClient.delete(`/accounts/${id}`)
}

export async function getAccountContacts(id: string): Promise<Contact[]> {
  const { data } = await apiClient.get<Contact[]>(`/accounts/${id}/contacts`)
  return data
}

export async function getAccountOpportunities(id: string): Promise<Opportunity[]> {
  const { data } = await apiClient.get<Opportunity[]>(`/accounts/${id}/opportunities`)
  return data
}

export async function getAccountTimeline(id: string): Promise<Activity[]> {
  const { data } = await apiClient.get<Activity[]>(`/accounts/${id}/timeline`)
  return data
}
