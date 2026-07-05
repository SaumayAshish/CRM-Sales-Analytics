import { Link, Outlet, useLocation } from "react-router-dom"
import {
  BarChart3,
  Building2,
  KanbanSquare,
  LayoutDashboard,
  LogOut,
  Settings,
  Users,
  UsersRound,
} from "lucide-react"

import { NotificationBell } from "@/components/shared/NotificationBell"
import { RoleGuard } from "@/components/shared/RoleGuard"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuth } from "@/hooks/useAuth"
import type { Role } from "@/types"

const NAV_ITEMS: { to: string; label: string; icon: typeof UsersRound; roles?: Role[] }[] = [
  { to: "/leads", label: "Leads", icon: UsersRound },
  { to: "/opportunities", label: "Pipeline", icon: KanbanSquare },
  { to: "/accounts", label: "Accounts", icon: Building2 },
  { to: "/contacts", label: "Contacts", icon: Users },
  { to: "/reports", label: "Reports", icon: BarChart3, roles: ["Admin", "Manager"] },
]

function breadcrumbFor(pathname: string): string {
  const segment = pathname.split("/").filter(Boolean)[0]
  const match = NAV_ITEMS.find((item) => item.to === `/${segment}`)
  if (match) return match.label
  if (segment === "settings") return "Settings"
  return "Dashboard"
}

export function DashboardShell() {
  const { user, role, logout } = useAuth()
  const location = useLocation()

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-56 flex-col border-r bg-muted/20 p-4 sm:flex">
        <div className="mb-6 flex items-center gap-2 px-2">
          <LayoutDashboard className="size-5" />
          <span className="font-semibold">Northwind CRM</span>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const active = location.pathname.startsWith(item.to)
            const link = (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                  active ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                }`}
              >
                <Icon className="size-4" />
                {item.label}
              </Link>
            )
            return item.roles ? (
              <RoleGuard key={item.to} allow={item.roles}>
                {link}
              </RoleGuard>
            ) : (
              link
            )
          })}
        </nav>
        <RoleGuard allow={["Admin"]}>
          <Link
            to="/settings"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-muted"
          >
            <Settings className="size-4" />
            Admin Console
          </Link>
        </RoleGuard>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b px-6 py-3">
          <div>
            <p className="text-xs text-muted-foreground">{breadcrumbFor(location.pathname)}</p>
            <h1 className="text-lg font-semibold">{breadcrumbFor(location.pathname)}</h1>
          </div>
          <div className="flex items-center gap-3">
            <NotificationBell />
            <Separator orientation="vertical" className="h-6" />
            <Link to="/settings" className="flex items-center gap-2">
              <Avatar className="size-8">
                <AvatarFallback>
                  {user ? `${user.first_name[0]}${user.last_name[0]}` : "?"}
                </AvatarFallback>
              </Avatar>
              <div className="hidden text-left text-sm sm:block">
                <p className="font-medium leading-none">{user ? `${user.first_name} ${user.last_name}` : "…"}</p>
                <p className="text-xs text-muted-foreground">{role}</p>
              </div>
            </Link>
            <Button variant="ghost" size="icon" onClick={() => void logout()} title="Sign out">
              <LogOut className="size-4" />
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
