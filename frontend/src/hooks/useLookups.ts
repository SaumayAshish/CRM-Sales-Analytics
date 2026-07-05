import { useQuery } from "@tanstack/react-query"

import {
  listActivityTypes,
  listLeadSources,
  listLossReasons,
  listPipelineStages,
  listRoles,
  listTeams,
} from "@/api/lookups"

export function useRoles() {
  return useQuery({ queryKey: ["lookups", "roles"], queryFn: listRoles, staleTime: Infinity })
}

export function useTeams() {
  return useQuery({ queryKey: ["lookups", "teams"], queryFn: listTeams, staleTime: Infinity })
}

export function useLeadSources() {
  return useQuery({ queryKey: ["lookups", "lead-sources"], queryFn: listLeadSources, staleTime: Infinity })
}

export function usePipelineStages() {
  return useQuery({ queryKey: ["lookups", "pipeline-stages"], queryFn: listPipelineStages, staleTime: Infinity })
}

export function useLossReasons() {
  return useQuery({ queryKey: ["lookups", "loss-reasons"], queryFn: listLossReasons, staleTime: Infinity })
}

export function useActivityTypes() {
  return useQuery({ queryKey: ["lookups", "activity-types"], queryFn: listActivityTypes, staleTime: Infinity })
}
