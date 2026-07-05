// Traces to: FR-06 (convert), FR-25/FR-53 (timeline), FR-51 (score breakdown).
import { useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"
import { ArrowLeft } from "lucide-react"

import { ActivityTimeline } from "@/components/shared/ActivityTimeline"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { RoleGuard } from "@/components/shared/RoleGuard"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useConvertLead, useLead, useLeadTimeline, useScoreBreakdown } from "@/hooks/useLeads"

export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: lead, isLoading } = useLead(id)
  const { data: timeline, isLoading: timelineLoading } = useLeadTimeline(id)
  const { data: breakdown } = useScoreBreakdown(id)
  const convertLead = useConvertLead()

  if (isLoading || !lead) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  async function handleConvert() {
    try {
      const result = await convertLead.mutateAsync(lead!.id)
      toast.success("Lead converted")
      navigate(`/accounts/${result.account_id}`)
    } catch {
      toast.error("Could not convert this lead (it may already be converted).")
    }
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => navigate("/leads")}>
        <ArrowLeft className="size-4" /> Back to Leads
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">
            {lead.first_name} {lead.last_name}
          </h2>
          <p className="text-muted-foreground">{lead.company}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge kind="score_band" value={lead.score_band} />
          <Badge variant="outline">Score {lead.score}</Badge>
          {!lead.is_converted && (
            <RoleGuard allow={["Admin", "Manager", "Rep"]}>
              <Button onClick={handleConvert} disabled={convertLead.isPending}>
                {convertLead.isPending ? "Converting…" : "Convert Lead"}
              </Button>
            </RoleGuard>
          )}
          {lead.is_converted && <Badge>Converted</Badge>}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>
              <span className="text-muted-foreground">Email: </span>
              {lead.email}
            </div>
            <div>
              <span className="text-muted-foreground">Phone: </span>
              {lead.phone ?? "—"}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Score Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {!breakdown || breakdown.matched_criteria.length === 0 ? (
              <p className="text-muted-foreground">No criteria matched.</p>
            ) : (
              breakdown.matched_criteria.map((c) => (
                <div key={c.field_name + c.comparison_value} className="flex justify-between">
                  <span className="text-muted-foreground">
                    {c.field_name} {c.operator} {c.comparison_value}
                  </span>
                  <span className={c.weight >= 0 ? "text-green-600" : "text-destructive"}>
                    {c.weight >= 0 ? "+" : ""}
                    {c.weight}
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <ActivityTimeline activities={timeline} isLoading={timelineLoading} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
