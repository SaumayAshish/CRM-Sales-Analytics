// Traces to: FR-17 (unified 360 view: company info + contacts + activities + opportunities).
import { useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, Star } from "lucide-react"

import { ActivityTimeline } from "@/components/shared/ActivityTimeline"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { DataTable, type DataTableColumn } from "@/components/shared/DataTable"
import { RoleGuard } from "@/components/shared/RoleGuard"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  useAccount,
  useAccountContacts,
  useAccountOpportunities,
  useAccountTimeline,
} from "@/hooks/useAccounts"
import { usePipelineStages } from "@/hooks/useLookups"
import { CreateContactDialog } from "@/pages/accounts/CreateContactDialog"
import type { Contact, Opportunity } from "@/types"

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value)
}

export function Account360Page() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: account, isLoading } = useAccount(id)
  const { data: contacts, isLoading: contactsLoading } = useAccountContacts(id)
  const { data: opportunities, isLoading: oppsLoading } = useAccountOpportunities(id)
  const { data: timeline, isLoading: timelineLoading } = useAccountTimeline(id)
  const { data: stages } = usePipelineStages()
  const stageNameById = new Map(stages?.map((s) => [s.id, s.name]) ?? [])

  if (isLoading || !account) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  const contactColumns: DataTableColumn<Contact>[] = [
    {
      key: "name",
      header: "Name",
      render: (c) => (
        <span className="flex items-center gap-2 font-medium">
          {c.first_name} {c.last_name}
          {c.is_primary && <Star className="size-3.5 fill-amber-400 text-amber-400" />}
        </span>
      ),
    },
    { key: "email", header: "Email", render: (c) => c.email },
    { key: "phone", header: "Phone", render: (c) => c.phone ?? "—" },
  ]

  const oppColumns: DataTableColumn<Opportunity>[] = [
    { key: "name", header: "Name", render: (o) => o.name },
    { key: "stage", header: "Stage", render: (o) => <StatusBadge kind="stage" value={stageNameById.get(o.stage_id) ?? "—"} /> },
    { key: "amount", header: "Amount", render: (o) => formatCurrency(o.amount) },
    { key: "weighted", header: "Weighted", render: (o) => formatCurrency(o.weighted_value) },
  ]

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => navigate("/accounts")}>
        <ArrowLeft className="size-4" /> Back to Accounts
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">{account.name}</h2>
          <p className="text-muted-foreground">{account.industry ?? "—"}</p>
        </div>
        {account.domain && <Badge variant="outline">{account.domain}</Badge>}
      </div>

      <Tabs defaultValue="contacts">
        <TabsList>
          <TabsTrigger value="contacts">Contacts ({contacts?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="opportunities">Opportunities ({opportunities?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>
        <TabsContent value="contacts" className="space-y-3">
          <div className="flex justify-end">
            <RoleGuard allow={["Admin", "Manager", "Rep"]}>
              <CreateContactDialog accountId={account.id} />
            </RoleGuard>
          </div>
          <DataTable
            columns={contactColumns}
            data={contacts}
            isLoading={contactsLoading}
            emptyMessage="No contacts yet."
            rowKey={(c) => c.id}
          />
        </TabsContent>
        <TabsContent value="opportunities">
          <DataTable
            columns={oppColumns}
            data={opportunities}
            isLoading={oppsLoading}
            emptyMessage="No opportunities yet."
            rowKey={(o) => o.id}
          />
        </TabsContent>
        <TabsContent value="timeline">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Activity Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <ActivityTimeline activities={timeline} isLoading={timelineLoading} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
