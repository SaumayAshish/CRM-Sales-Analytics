// Traces to: FR-45 (profile/role info), BR-23 (quota display), BR-24/FR-66
// (company-wide quarterly target, Admin-editable).
import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { RoleGuard } from "@/components/shared/RoleGuard"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { getRepPerformance } from "@/api/analytics"
import { getCurrentCompanyTarget, updateCurrentCompanyTarget } from "@/api/company_targets"
import { useAuth } from "@/hooks/useAuth"

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value)
}

export function SettingsPage() {
  const { user, role } = useAuth()
  const queryClient = useQueryClient()
  const { data: repPerformance } = useQuery({
    queryKey: ["analytics", "rep-performance"],
    queryFn: getRepPerformance,
    enabled: role === "Admin" || role === "Manager" || role === "Rep",
  })
  const { data: companyTarget } = useQuery({
    queryKey: ["company-target", "current"],
    queryFn: getCurrentCompanyTarget,
    enabled: role === "Admin",
  })
  const [targetInput, setTargetInput] = useState("")
  const updateTarget = useMutation({
    mutationFn: (amount: number) => updateCurrentCompanyTarget(amount),
    onSuccess: () => {
      toast.success("Quarterly target updated.")
      queryClient.invalidateQueries({ queryKey: ["company-target"] })
    },
  })

  const myPerformance = repPerformance?.find((r) => r.user_id === user?.id)

  return (
    <div className="max-w-2xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profile</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-4">
          <Avatar className="size-14">
            <AvatarFallback className="text-lg">
              {user ? `${user.first_name[0]}${user.last_name[0]}` : "?"}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
            <Badge variant="outline" className="mt-1">
              {role}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <RoleGuard allow={["Manager", "Rep"]}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quota Attainment</CardTitle>
          </CardHeader>
          <CardContent>
            {user?.quota == null ? (
              <p className="text-sm text-muted-foreground">
                No quota has been set for your account yet -- this KPI is not applicable until one is.
              </p>
            ) : (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Quota</span>
                  <span>{formatCurrency(user.quota)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Closed Won Revenue (this quarter)</span>
                  <span>
                    {myPerformance ? formatCurrency(Number(myPerformance.closed_won_revenue_current_quarter)) : "—"}
                  </span>
                </div>
                <div className="flex justify-between font-medium">
                  <span>Attainment</span>
                  <span>
                    {myPerformance?.quota_attainment
                      ? `${(Number(myPerformance.quota_attainment) * 100).toFixed(1)}%`
                      : "—"}
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </RoleGuard>

      <RoleGuard allow={["Admin"]}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Company Quarterly Target</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Backs the Pipeline Coverage Ratio KPI (Total Open Pipeline Value ÷ this target).
              Distinct from an individual rep's quota above.
            </p>
            <div className="flex items-end gap-2">
              <div className="flex-1 space-y-2">
                <Label>Target for quarter starting {companyTarget?.quarter_start ?? "—"}</Label>
                <Input
                  type="number"
                  placeholder={companyTarget ? String(companyTarget.target_amount) : "Loading…"}
                  value={targetInput}
                  onChange={(e) => setTargetInput(e.target.value)}
                />
              </div>
              <Button
                onClick={() => {
                  const amount = Number(targetInput)
                  if (!Number.isFinite(amount) || amount < 0) {
                    toast.error("Enter a valid non-negative amount.")
                    return
                  }
                  updateTarget.mutate(amount)
                }}
                disabled={updateTarget.isPending || !targetInput}
              >
                {updateTarget.isPending ? "Saving…" : "Save"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Admin Console</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              User management, pipeline stage configuration, and scoring rule configuration are
              available via the API (`/users`, `/pipeline/stages`, `/lead-scoring/rules`,
              `/workflows`) -- a dedicated Admin UI for these is scoped for a future phase.
            </p>
          </CardContent>
        </Card>
      </RoleGuard>
    </div>
  )
}
