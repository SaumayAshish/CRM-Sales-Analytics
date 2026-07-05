// Handles both FR-12 (loss reason required for Closed Lost) and
// FR-46/47 (override reason required for a non-standard transition) --
// shown reactively after a 422 from the first attempt, since the client
// doesn't know in advance which one the backend will require.
import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useLossReasons } from "@/hooks/useLookups"
import { useAdvanceStage } from "@/hooks/useOpportunities"
import type { PipelineStageOption } from "@/types"

interface StageChangeDialogProps {
  opportunityId: string | null
  targetStage: PipelineStageOption | null
  onClose: () => void
}

export function StageChangeDialog({ opportunityId, targetStage, onClose }: StageChangeDialogProps) {
  const { data: lossReasons } = useLossReasons()
  const advanceStage = useAdvanceStage()
  const [lossReasonId, setLossReasonId] = useState<string>("")
  const [overrideReason, setOverrideReason] = useState("")

  const isClosedLost = targetStage?.name === "Closed Lost"

  async function handleConfirm() {
    if (!opportunityId || !targetStage) return
    try {
      await advanceStage.mutateAsync({
        id: opportunityId,
        payload: {
          stage_id: targetStage.id,
          loss_reason_id: lossReasonId || undefined,
          override_reason: overrideReason || undefined,
        },
      })
      toast.success(`Moved to ${targetStage.name}`)
      setLossReasonId("")
      setOverrideReason("")
      onClose()
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Could not update the stage."
      toast.error(detail)
    }
  }

  return (
    <Dialog open={!!targetStage} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Move to {targetStage?.name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {isClosedLost && (
            <div className="space-y-2">
              <Label>Loss reason (required)</Label>
              <Select value={lossReasonId} onValueChange={setLossReasonId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a reason" />
                </SelectTrigger>
                <SelectContent>
                  {lossReasons?.map((r) => (
                    <SelectItem key={r.id} value={r.id}>
                      {r.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="space-y-2">
            <Label>Override reason (only needed for a non-standard transition)</Label>
            <Textarea
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="e.g. Deal moved unusually fast, confirmed with customer"
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleConfirm} disabled={advanceStage.isPending}>
            {advanceStage.isPending ? "Saving…" : "Confirm"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
