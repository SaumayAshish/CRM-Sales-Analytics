import { apiClient } from "@/api/client"
import type { Contact } from "@/types"

export interface ContactFilters {
  account_id?: string
  email?: string
  page?: number
  page_size?: number
}

export interface ContactCreatePayload {
  account_id: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  is_primary?: boolean
}

export type ContactUpdatePayload = Partial<Omit<ContactCreatePayload, "account_id">>

export async function listContacts(filters: ContactFilters = {}): Promise<Contact[]> {
  const { data } = await apiClient.get<Contact[]>("/contacts", { params: filters })
  return data
}

export async function getContact(id: string): Promise<Contact> {
  const { data } = await apiClient.get<Contact>(`/contacts/${id}`)
  return data
}

export async function createContact(payload: ContactCreatePayload): Promise<Contact> {
  const { data } = await apiClient.post<Contact>("/contacts", payload)
  return data
}

export async function updateContact(id: string, payload: ContactUpdatePayload): Promise<Contact> {
  const { data } = await apiClient.patch<Contact>(`/contacts/${id}`, payload)
  return data
}

export async function deleteContact(id: string): Promise<void> {
  await apiClient.delete(`/contacts/${id}`)
}
