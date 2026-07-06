import { apiClient } from "@/api/client"
import type { CompanyTarget } from "@/types"

export async function getCurrentCompanyTarget(): Promise<CompanyTarget> {
  const { data } = await apiClient.get<CompanyTarget>("/company-targets/current")
  return data
}

export async function updateCurrentCompanyTarget(targetAmount: number): Promise<CompanyTarget> {
  const { data } = await apiClient.patch<CompanyTarget>("/company-targets/current", {
    target_amount: targetAmount,
  })
  return data
}
