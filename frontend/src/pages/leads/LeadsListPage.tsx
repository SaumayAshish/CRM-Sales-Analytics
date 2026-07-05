// Traces to: FR-01, FR-08 (unassigned queue), FR-22-style search/filter.
// Note: the backend leads endpoint filters by source_id/assigned_to/
// unassigned-status server-side; free-text search below filters the
// currently-loaded page client-side only (no full-text search endpoint
// exists yet) -- labeled here so this limitation isn't silently assumed away.
import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { CreateLeadDialog } from "@/pages/leads/CreateLeadDialog"
import { RoleGuard } from "@/components/shared/RoleGuard"
import { DataTable, type DataTableColumn } from "@/components/shared/DataTable"
import { StatusBadge } from "@/components/shared/StatusBadge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useLeadsList } from "@/hooks/useLeads"
import { useLeadSources } from "@/hooks/useLookups"
import type { Lead } from "@/types"

export function LeadsListPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [showUnassigned, setShowUnassigned] = useState(false)
  const [page, setPage] = useState(1)

  const { data: leads, isLoading } = useLeadsList({
    status_unassigned: showUnassigned || undefined,
    page,
    page_size: 50,
  })
  const { data: sources } = useLeadSources()
  const sourceNameById = new Map(sources?.map((s) => [s.id, s.name]) ?? [])

  const filtered = leads?.filter((lead) => {
    if (!search) return true
    const haystack = `${lead.first_name} ${lead.last_name} ${lead.company} ${lead.email}`.toLowerCase()
    return haystack.includes(search.toLowerCase())
  })

  const columns: DataTableColumn<Lead>[] = [
    {
      key: "name",
      header: "Name",
      render: (l) => (
        <span className="font-medium">
          {l.first_name} {l.last_name}
        </span>
      ),
      sortValue: (l) => `${l.first_name} ${l.last_name}`,
    },
    { key: "company", header: "Company", render: (l) => l.company, sortValue: (l) => l.company },
    { key: "email", header: "Email", render: (l) => l.email },
    { key: "source", header: "Source", render: (l) => sourceNameById.get(l.source_id) ?? "—" },
    {
      key: "score",
      header: "Score",
      render: (l) => (
        <span className="flex items-center gap-2">
          <StatusBadge kind="score_band" value={l.score_band} />
          <span className="text-xs text-muted-foreground">{l.score}</span>
        </span>
      ),
      sortValue: (l) => l.score,
    },
    {
      key: "status",
      header: "Status",
      render: (l) => (l.is_converted ? "Converted" : l.assigned_to ? "Assigned" : "Unassigned"),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search name, company, email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64"
          />
          <RoleGuard allow={["Admin", "Manager"]}>
            <Button
              variant={showUnassigned ? "default" : "outline"}
              onClick={() => setShowUnassigned((v) => !v)}
            >
              Unassigned queue
            </Button>
          </RoleGuard>
        </div>
        <RoleGuard allow={["Admin", "Manager", "Rep"]}>
          <CreateLeadDialog />
        </RoleGuard>
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        isLoading={isLoading}
        emptyMessage="No leads match your filters."
        rowKey={(l) => l.id}
        onRowClick={(l) => navigate(`/leads/${l.id}`)}
      />

      <div className="flex justify-end gap-2">
        <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={(leads?.length ?? 0) < 50}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  )
}
