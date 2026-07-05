import { useNavigate } from "react-router-dom"
import { Star } from "lucide-react"

import { DataTable, type DataTableColumn } from "@/components/shared/DataTable"
import { useAccountsList } from "@/hooks/useAccounts"
import { useContactsList } from "@/hooks/useContacts"
import type { Contact } from "@/types"

export function ContactsListPage() {
  const navigate = useNavigate()
  const { data: contacts, isLoading } = useContactsList({ page_size: 100 })
  const { data: accounts } = useAccountsList({ page_size: 100 })
  const accountNameById = new Map(accounts?.map((a) => [a.id, a.name]) ?? [])

  const columns: DataTableColumn<Contact>[] = [
    {
      key: "name",
      header: "Name",
      render: (c) => (
        <span className="flex items-center gap-2 font-medium">
          {c.first_name} {c.last_name}
          {c.is_primary && <Star className="size-3.5 fill-amber-400 text-amber-400" />}
        </span>
      ),
      sortValue: (c) => `${c.first_name} ${c.last_name}`,
    },
    { key: "account", header: "Account", render: (c) => accountNameById.get(c.account_id) ?? "—" },
    { key: "email", header: "Email", render: (c) => c.email },
    { key: "phone", header: "Phone", render: (c) => c.phone ?? "—" },
  ]

  return (
    <DataTable
      columns={columns}
      data={contacts}
      isLoading={isLoading}
      emptyMessage="No contacts yet."
      rowKey={(c) => c.id}
      onRowClick={(c) => navigate(`/accounts/${c.account_id}`)}
    />
  )
}
