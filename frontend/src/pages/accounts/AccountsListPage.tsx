import { useNavigate } from "react-router-dom"

import { CreateAccountDialog } from "@/pages/accounts/CreateAccountDialog"
import { DataTable, type DataTableColumn } from "@/components/shared/DataTable"
import { RoleGuard } from "@/components/shared/RoleGuard"
import { useAccountsList } from "@/hooks/useAccounts"
import type { Account } from "@/types"

export function AccountsListPage() {
  const navigate = useNavigate()
  const { data: accounts, isLoading } = useAccountsList({ page_size: 100 })

  const columns: DataTableColumn<Account>[] = [
    { key: "name", header: "Name", render: (a) => <span className="font-medium">{a.name}</span>, sortValue: (a) => a.name },
    { key: "domain", header: "Domain", render: (a) => a.domain ?? "—" },
    { key: "industry", header: "Industry", render: (a) => a.industry ?? "—" },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <RoleGuard allow={["Admin", "Manager", "Rep"]}>
          <CreateAccountDialog />
        </RoleGuard>
      </div>
      <DataTable
        columns={columns}
        data={accounts}
        isLoading={isLoading}
        emptyMessage="No accounts yet."
        rowKey={(a) => a.id}
        onRowClick={(a) => navigate(`/accounts/${a.id}`)}
      />
    </div>
  )
}
