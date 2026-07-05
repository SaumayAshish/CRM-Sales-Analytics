// Traces to: FR-19 (duplicate-domain warning surfaced as a 409, with a
// second confirmed attempt sending override_duplicate_warning + reason).
import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

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
import { Textarea } from "@/components/ui/textarea"
import { useAuth } from "@/hooks/useAuth"
import { useCreateAccount } from "@/hooks/useAccounts"
import { Plus } from "lucide-react"

const schema = z.object({
  name: z.string().min(1, "Required"),
  domain: z.string().optional(),
  industry: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function CreateAccountDialog() {
  const [open, setOpen] = useState(false)
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null)
  const [overrideReason, setOverrideReason] = useState("")
  const { user } = useAuth()
  const createAccount = useCreateAccount()

  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  async function submit(values: FormValues, override = false) {
    if (!user) return
    try {
      await createAccount.mutateAsync({
        name: values.name,
        domain: values.domain || undefined,
        industry: values.industry || undefined,
        owner_id: user.id,
        override_duplicate_warning: override,
        override_reason: override ? overrideReason : undefined,
      })
      toast.success("Account created")
      reset()
      setDuplicateWarning(null)
      setOverrideReason("")
      setOpen(false)
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.status
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      if (status === 409 && detail) {
        setDuplicateWarning(detail)
      } else {
        toast.error(detail ?? "Could not create account.")
      }
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (!o) {
          reset()
          setDuplicateWarning(null)
        }
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> New Account
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Account</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit((v) => submit(v))} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Company name</Label>
            <Input id="name" {...register("name")} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="domain">Domain (optional)</Label>
            <Input id="domain" placeholder="example.com" {...register("domain")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="industry">Industry (optional)</Label>
            <Input id="industry" {...register("industry")} />
          </div>

          {duplicateWarning && (
            <div className="space-y-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm dark:border-amber-800 dark:bg-amber-950">
              <p className="text-amber-800 dark:text-amber-300">{duplicateWarning}</p>
              <Label>Override reason (required to proceed)</Label>
              <Textarea value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} />
              <Button
                type="button"
                variant="secondary"
                disabled={!overrideReason || createAccount.isPending}
                onClick={() => submit(getValues(), true)}
              >
                Create anyway
              </Button>
            </div>
          )}

          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating…" : "Create Account"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
