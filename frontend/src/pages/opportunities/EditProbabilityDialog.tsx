// Traces to: FR-65 (per-deal probability override, distinct from the
// stage-default probability set automatically on every stage
// transition). Closes the Commit Forecast KPI gap flagged in
// docs/PHASE_REPORTS/phase_5.md -- a rep can now flag a specific deal
// as higher-confidence than its stage would otherwise imply.
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useUpdateOpportunity } from "@/hooks/useOpportunities"
import type { Opportunity } from "@/types"

interface EditProbabilityDialogProps {
  opportunity: Opportunity | null
  onClose: () => void
}

export function EditProbabilityDialog({ opportunity, onClose }: EditProbabilityDialogProps) {
  const updateOpportunity = useUpdateOpportunity()
  const [probabilityPercent, setProbabilityPercent] = useState("")

  useEffect(() => {
    if (opportunity) {
      setProbabilityPercent(String(Math.round(opportunity.probability * 100)))
    }
  }, [opportunity])

  async function handleSave() {
    if (!opportunity) return
    const percent = Number(probabilityPercent)
    if (!Number.isFinite(percent) || percent < 0 || percent > 100) {
      toast.error("Probability must be a number between 0 and 100.")
      return
    }
    try {
      await updateOpportunity.mutateAsync({
        id: opportunity.id,
        payload: { probability: percent / 100 },
      })
      toast.success("Probability updated.")
      onClose()
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Could not update probability."
      toast.error(detail)
    }
  }

  return (
    <Dialog open={!!opportunity} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit win probability</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {opportunity?.name} — stage default probability is set automatically on every stage
            change; override it here to reflect deal-specific confidence (e.g. a verbal commitment).
          </p>
          <div className="space-y-2">
            <Label>Probability (%)</Label>
            <Input
              type="number"
              min={0}
              max={100}
              value={probabilityPercent}
              onChange={(e) => setProbabilityPercent(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSave} disabled={updateOpportunity.isPending}>
            {updateOpportunity.isPending ? "Saving…" : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
