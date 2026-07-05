import { apiClient } from "@/api/client"
import type {
  ActivityTypeOption,
  LeadSourceOption,
  LossReasonOption,
  PipelineStageOption,
  RoleOption,
  TeamOption,
} from "@/types"

export async function listRoles(): Promise<RoleOption[]> {
  return (await apiClient.get<RoleOption[]>("/lookups/roles")).data
}

export async function listTeams(): Promise<TeamOption[]> {
  return (await apiClient.get<TeamOption[]>("/lookups/teams")).data
}

export async function listLeadSources(): Promise<LeadSourceOption[]> {
  return (await apiClient.get<LeadSourceOption[]>("/lookups/lead-sources")).data
}

export async function listPipelineStages(): Promise<PipelineStageOption[]> {
  return (await apiClient.get<PipelineStageOption[]>("/lookups/pipeline-stages")).data
}

export async function listLossReasons(): Promise<LossReasonOption[]> {
  return (await apiClient.get<LossReasonOption[]>("/lookups/loss-reasons")).data
}

export async function listActivityTypes(): Promise<ActivityTypeOption[]> {
  return (await apiClient.get<ActivityTypeOption[]>("/lookups/activity-types")).data
}
