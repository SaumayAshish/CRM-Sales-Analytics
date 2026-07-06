// Traces to: FR-10 (Kanban grouped by stage), FR-11 (drag-and-drop stage
// transitions), FR-15 (weighted value). Uses the native HTML5 drag-and-drop
// API rather than a new dependency, per the "no new state libraries without
// approval" instruction (a DnD library isn't a state library, but kept out
// anyway to minimize new dependencies for a board of this size).
import { useState } from "react"
import { Pencil } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { RoleGuard } from "@/components/shared/RoleGuard"
import { useAuth } from "@/hooks/useAuth"
import { usePipelineStages } from "@/hooks/useLookups"
import { useOpportunitiesList } from "@/hooks/useOpportunities"
import { CreateOpportunityDialog } from "@/pages/opportunities/CreateOpportunityDialog"
import { EditProbabilityDialog } from "@/pages/opportunities/EditProbabilityDialog"
import { StageChangeDialog } from "@/pages/opportunities/StageChangeDialog"
import type { Opportunity, PipelineStageOption } from "@/types"

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value)
}

export function KanbanPage() {
  const { role } = useAuth()
  const canEdit = role !== "Viewer" // BR-12: Viewer is read-only everywhere.
  const { data: stages, isLoading: stagesLoading } = usePipelineStages()
  // Kanban needs every open/closed deal in view to render accurate per-stage
  // totals -- a lower page_size here silently undercounted once total
  // opportunities exceeded it (found via live testing, fixed alongside the
  // API's matching le=200 cap). 2000 comfortably covers current seed volume
  // (1,540); a true Kanban-scale fix (virtualized/paginated columns) is a
  // reasonable follow-up if this data volume grows another order of magnitude.
  const { data: opportunities, isLoading: oppsLoading } = useOpportunitiesList({ page_size: 2000 })
  const [draggedId, setDraggedId] = useState<string | null>(null)
  const [pendingTarget, setPendingTarget] = useState<{ opportunityId: string; stage: PipelineStageOption } | null>(null)
  const [editingProbability, setEditingProbability] = useState<Opportunity | null>(null)

  if (stagesLoading || oppsLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    )
  }

  const sortedStages = [...(stages ?? [])].sort((a, b) => a.sort_order - b.sort_order)
  const opportunitiesByStage = new Map<string, Opportunity[]>()
  for (const opp of opportunities ?? []) {
    const list = opportunitiesByStage.get(opp.stage_id) ?? []
    list.push(opp)
    opportunitiesByStage.set(opp.stage_id, list)
  }

  function handleDrop(stage: PipelineStageOption) {
    if (!draggedId) return
    const opp = opportunities?.find((o) => o.id === draggedId)
    if (opp && opp.stage_id !== stage.id) {
      setPendingTarget({ opportunityId: draggedId, stage })
    }
    setDraggedId(null)
  }

  return (
    <>
      <div className="mb-4 flex justify-end">
        <RoleGuard allow={["Admin", "Manager", "Rep"]}>
          <CreateOpportunityDialog />
        </RoleGuard>
      </div>
      <div className="grid grid-cols-1 gap-4 overflow-x-auto sm:grid-cols-3 lg:grid-cols-6">
        {sortedStages.map((stage) => {
          const stageOpps = opportunitiesByStage.get(stage.id) ?? []
          const totalValue = stageOpps.reduce((sum, o) => sum + o.amount, 0)

          return (
            <div
              key={stage.id}
              className="flex min-w-[220px] flex-col rounded-md border bg-muted/20"
              onDragOver={(e) => canEdit && e.preventDefault()}
              onDrop={() => canEdit && handleDrop(stage)}
            >
              <div className="border-b p-3">
                <h3 className="text-sm font-semibold">{stage.name}</h3>
                <p className="text-xs text-muted-foreground">
                  {stageOpps.length} deals · {formatCurrency(totalValue)}
                </p>
              </div>
              <div className="flex flex-1 flex-col gap-2 p-2">
                {stageOpps.map((opp) => (
                  <Card
                    key={opp.id}
                    draggable={canEdit}
                    onDragStart={() => canEdit && setDraggedId(opp.id)}
                    className={canEdit ? "cursor-grab active:cursor-grabbing" : ""}
                  >
                    <CardHeader className="p-3 pb-0">
                      <p className="text-sm font-medium leading-tight">{opp.name}</p>
                    </CardHeader>
                    <CardContent className="p-3 pt-1">
                      <div className="flex items-center justify-between">
                        <Badge variant="outline">{formatCurrency(opp.amount)}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatCurrency(opp.weighted_value)} wtd
                        </span>
                      </div>
                      <div className="mt-1 flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">
                          {Math.round(opp.probability * 100)}% probability
                        </span>
                        {canEdit && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-6"
                            onClick={(e) => {
                              e.stopPropagation()
                              setEditingProbability(opp)
                            }}
                          >
                            <Pencil className="size-3" />
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      <StageChangeDialog
        opportunityId={pendingTarget?.opportunityId ?? null}
        targetStage={pendingTarget?.stage ?? null}
        onClose={() => setPendingTarget(null)}
      />
      <EditProbabilityDialog opportunity={editingProbability} onClose={() => setEditingProbability(null)} />
    </>
  )
}
