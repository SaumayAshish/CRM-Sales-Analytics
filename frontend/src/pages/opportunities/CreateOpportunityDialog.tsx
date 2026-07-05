// Traces to: FR-13 (account_id/owner_id required), FR-09 (initial stage
// must be a real pipeline stage).
import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useAccountsList } from "@/hooks/useAccounts"
import { useAuth } from "@/hooks/useAuth"
import { usePipelineStages } from "@/hooks/useLookups"
import { useCreateOpportunity } from "@/hooks/useOpportunities"

const schema = z.object({
  name: z.string().min(1, "Required"),
  account_id: z.string().min(1, "Select an account"),
  amount: z.coerce.number().min(0, "Must be zero or more"),
  expected_close_date: z.string().min(1, "Required"),
})

type FormValues = z.infer<typeof schema>

export function CreateOpportunityDialog() {
  const [open, setOpen] = useState(false)
  const { user } = useAuth()
  const { data: accounts } = useAccountsList({ page_size: 100 })
  const { data: stages } = usePipelineStages()
  const createOpportunity = useCreateOpportunity()

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormValues) {
    if (!user) return
    const firstStage = [...(stages ?? [])].sort((a, b) => a.sort_order - b.sort_order)[0]
    if (!firstStage) {
      toast.error("No pipeline stages configured.")
      return
    }
    try {
      await createOpportunity.mutateAsync({
        name: values.name,
        account_id: values.account_id,
        owner_id: user.id,
        stage_id: firstStage.id,
        amount: values.amount,
        probability: firstStage.default_probability,
        expected_close_date: values.expected_close_date,
      })
      toast.success("Opportunity created")
      reset()
      setOpen(false)
    } catch {
      toast.error("Could not create opportunity.")
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> New Opportunity
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Opportunity</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="o_name">Name</Label>
            <Input id="o_name" {...register("name")} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label>Account</Label>
            <Select value={watch("account_id")} onValueChange={(v) => setValue("account_id", v)}>
              <SelectTrigger>
                <SelectValue placeholder="Select an account" />
              </SelectTrigger>
              <SelectContent>
                {accounts?.map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.account_id && <p className="text-sm text-destructive">{errors.account_id.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="o_amount">Amount (USD)</Label>
            <Input id="o_amount" type="number" step="0.01" {...register("amount")} />
            {errors.amount && <p className="text-sm text-destructive">{errors.amount.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="o_close_date">Expected close date</Label>
            <Input id="o_close_date" type="date" {...register("expected_close_date")} />
            {errors.expected_close_date && (
              <p className="text-sm text-destructive">{errors.expected_close_date.message}</p>
            )}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating…" : "Create Opportunity"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
