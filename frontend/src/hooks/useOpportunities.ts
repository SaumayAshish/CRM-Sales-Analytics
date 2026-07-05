import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  advanceStage,
  createOpportunity,
  deleteOpportunity,
  getOpportunity,
  getStageHistory,
  listOpportunities,
  updateOpportunity,
  type OpportunityCreatePayload,
  type OpportunityFilters,
  type OpportunityUpdatePayload,
  type StageChangePayload,
} from "@/api/opportunities"

export function useOpportunitiesList(filters: OpportunityFilters = {}) {
  return useQuery({ queryKey: ["opportunities", filters], queryFn: () => listOpportunities(filters) })
}

export function useOpportunity(id: string | undefined) {
  return useQuery({ queryKey: ["opportunities", id], queryFn: () => getOpportunity(id!), enabled: !!id })
}

export function useStageHistory(id: string | undefined) {
  return useQuery({ queryKey: ["opportunities", id, "stage-history"], queryFn: () => getStageHistory(id!), enabled: !!id })
}

export function useCreateOpportunity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: OpportunityCreatePayload) => createOpportunity(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
  })
}

export function useUpdateOpportunity(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: OpportunityUpdatePayload) => updateOpportunity(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
  })
}

export function useDeleteOpportunity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteOpportunity(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
  })
}

export function useAdvanceStage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: StageChangePayload }) => advanceStage(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["opportunities"] }),
  })
}
