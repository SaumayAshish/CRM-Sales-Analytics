import { apiClient } from "@/api/client"
import type { PipelineSummaryRow, RepPerformanceRow } from "@/types"

export async function getPipelineSummary(): Promise<PipelineSummaryRow[]> {
  const { data } = await apiClient.get<PipelineSummaryRow[]>("/analytics/pipeline-summary")
  return data
}

export async function getRepPerformance(): Promise<RepPerformanceRow[]> {
  const { data } = await apiClient.get<RepPerformanceRow[]>("/analytics/rep-performance")
  return data
}
