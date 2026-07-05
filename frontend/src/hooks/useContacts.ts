import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  createContact,
  deleteContact,
  getContact,
  listContacts,
  updateContact,
  type ContactCreatePayload,
  type ContactFilters,
  type ContactUpdatePayload,
} from "@/api/contacts"

export function useContactsList(filters: ContactFilters = {}) {
  return useQuery({ queryKey: ["contacts", filters], queryFn: () => listContacts(filters) })
}

export function useContact(id: string | undefined) {
  return useQuery({ queryKey: ["contacts", id], queryFn: () => getContact(id!), enabled: !!id })
}

export function useCreateContact() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ContactCreatePayload) => createContact(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["contacts"] }),
  })
}

export function useUpdateContact(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ContactUpdatePayload) => updateContact(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["contacts"] }),
  })
}

export function useDeleteContact() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteContact(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["contacts"] }),
  })
}
