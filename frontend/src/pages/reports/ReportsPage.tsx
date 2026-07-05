// Traces to: FR-28-FR-32 (4 Power BI dashboards), Phase 5 embedding decision
// (screenshot gallery, not publish-to-web -- see analytics/README.md SS5).
// Images are placed by hand into public/reports/ after building the
// dashboards in Power BI Desktop (see analytics/powerbi_dashboards/
// BUILD_INSTRUCTIONS.md) -- this page can't generate them itself.
import { useState } from "react"
import { ImageOff } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { RoleGuard } from "@/components/shared/RoleGuard"

interface DashboardEntry {
  key: string
  title: string
  description: string
  image: string
}

const DASHBOARDS: DashboardEntry[] = [
  {
    key: "executive-summary",
    title: "Executive Summary",
    description:
      "Total pipeline value, revenue vs. target, 6-month win rate trend, top 5 accounts, and sales funnel conversion.",
    image: "/reports/executive_summary.png",
  },
  {
    key: "pipeline-health",
    title: "Pipeline Health",
    description:
      "Pipeline by stage, average deal size, stage aging, forecast by month, and win probability distribution.",
    image: "/reports/pipeline_health.png",
  },
  {
    key: "rep-performance",
    title: "Rep Performance",
    description:
      "Leaderboard, quota attainment, activity volume, conversion rate, and sales cycle length per rep.",
    image: "/reports/rep_performance.png",
  },
  {
    key: "lead-funnel",
    title: "Lead Funnel",
    description:
      "Lead source ROI, scoring distribution, response time by rep, and lead aging.",
    image: "/reports/lead_funnel.png",
  },
]

function DashboardThumbnail({ dashboard }: { dashboard: DashboardEntry }) {
  const [imageFailed, setImageFailed] = useState(false)

  if (imageFailed) {
    return (
      <div className="flex aspect-video flex-col items-center justify-center gap-2 rounded-md border border-dashed bg-muted/30 text-center">
        <ImageOff className="size-8 text-muted-foreground" />
        <p className="px-4 text-sm text-muted-foreground">
          Not yet exported — see <code>analytics/powerbi_dashboards/BUILD_INSTRUCTIONS.md</code>
        </p>
      </div>
    )
  }

  return (
    <img
      src={dashboard.image}
      alt={`${dashboard.title} dashboard screenshot`}
      className="aspect-video w-full rounded-md border object-cover"
      onError={() => setImageFailed(true)}
    />
  )
}

export function ReportsPage() {
  const [openDashboard, setOpenDashboard] = useState<DashboardEntry | null>(null)

  return (
    <RoleGuard
      allow={["Admin", "Manager"]}
      fallback={
        <p className="text-sm text-muted-foreground">
          You don't have access to analytics reports. Contact your Manager or Admin.
        </p>
      }
    >
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold">Analytics Reports</h2>
          <p className="text-sm text-muted-foreground">
            Power BI dashboards built on the SQL analytics layer (<code>analytics/sql_queries/</code>).
            Every visual traces to a documented KPI — see <code>analytics/KPI_CROSS_CHECK.md</code>.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {DASHBOARDS.map((dashboard) => (
            <Card
              key={dashboard.key}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => setOpenDashboard(dashboard)}
            >
              <CardHeader>
                <CardTitle className="text-base">{dashboard.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <DashboardThumbnail dashboard={dashboard} />
                <p className="text-sm text-muted-foreground">{dashboard.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Dialog open={!!openDashboard} onOpenChange={(open) => !open && setOpenDashboard(null)}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>{openDashboard?.title}</DialogTitle>
            </DialogHeader>
            {openDashboard && <DashboardThumbnail dashboard={openDashboard} />}
          </DialogContent>
        </Dialog>
      </div>
    </RoleGuard>
  )
}
