import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  createAccount,
  deleteAccount,
  getAccount,
  getAccountContacts,
  getAccountOpportunities,
  getAccountTimeline,
  listAccounts,
  updateAccount,
  type AccountCreatePayload,
  type AccountFilters,
  type AccountUpdatePayload,
} from "@/api/accounts"

export function useAccountsList(filters: AccountFilters = {}) {
  return useQuery({ queryKey: ["accounts", filters], queryFn: () => listAccounts(filters) })
}

export function useAccount(id: string | undefined) {
  return useQuery({ queryKey: ["accounts", id], queryFn: () => getAccount(id!), enabled: !!id })
}

export function useAccountContacts(id: string | undefined) {
  return useQuery({ queryKey: ["accounts", id, "contacts"], queryFn: () => getAccountContacts(id!), enabled: !!id })
}

export function useAccountOpportunities(id: string | undefined) {
  return useQuery({ queryKey: ["accounts", id, "opportunities"], queryFn: () => getAccountOpportunities(id!), enabled: !!id })
}

export function useAccountTimeline(id: string | undefined) {
  return useQuery({ queryKey: ["accounts", id, "timeline"], queryFn: () => getAccountTimeline(id!), enabled: !!id })
}

export function useCreateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AccountCreatePayload) => createAccount(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  })
}

export function useUpdateAccount(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AccountUpdatePayload) => updateAccount(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  })
}

export function useDeleteAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteAccount(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  })
}
