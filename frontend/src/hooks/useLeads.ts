import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  assignLead,
  convertLead,
  createLead,
  deleteLead,
  getLead,
  getLeadTimeline,
  getScoreBreakdown,
  listLeads,
  updateLead,
  type LeadCreatePayload,
  type LeadFilters,
  type LeadUpdatePayload,
} from "@/api/leads"

export function useLeadsList(filters: LeadFilters) {
  return useQuery({ queryKey: ["leads", filters], queryFn: () => listLeads(filters) })
}

export function useLead(id: string | undefined) {
  return useQuery({ queryKey: ["leads", id], queryFn: () => getLead(id!), enabled: !!id })
}

export function useLeadTimeline(id: string | undefined) {
  return useQuery({ queryKey: ["leads", id, "timeline"], queryFn: () => getLeadTimeline(id!), enabled: !!id })
}

export function useScoreBreakdown(id: string | undefined) {
  return useQuery({ queryKey: ["leads", id, "score-breakdown"], queryFn: () => getScoreBreakdown(id!), enabled: !!id })
}

export function useCreateLead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: LeadCreatePayload) => createLead(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leads"] }),
  })
}

export function useUpdateLead(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: LeadUpdatePayload) => updateLead(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] })
    },
  })
}

export function useDeleteLead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteLead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leads"] }),
  })
}

export function useAssignLead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, assignedTo }: { id: string; assignedTo: string }) => assignLead(id, assignedTo),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leads"] }),
  })
}

export function useConvertLead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => convertLead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] })
      queryClient.invalidateQueries({ queryKey: ["accounts"] })
      queryClient.invalidateQueries({ queryKey: ["opportunities"] })
    },
  })
}
