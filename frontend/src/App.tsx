import { Navigate, Route, Routes } from "react-router-dom"

import { ProtectedRoute } from "@/components/shared/ProtectedRoute"
import { useAuth } from "@/hooks/useAuth"
import { Account360Page } from "@/pages/accounts/Account360Page"
import { AccountsListPage } from "@/pages/accounts/AccountsListPage"
import { ForgotPasswordStub } from "@/pages/auth/ForgotPasswordStub"
import { LoginPage } from "@/pages/auth/LoginPage"
import { ContactsListPage } from "@/pages/contacts/ContactsListPage"
import { DashboardShell } from "@/pages/dashboard/DashboardShell"
import { LeadDetailPage } from "@/pages/leads/LeadDetailPage"
import { LeadsListPage } from "@/pages/leads/LeadsListPage"
import { KanbanPage } from "@/pages/opportunities/KanbanPage"
import { SettingsPage } from "@/pages/settings/SettingsPage"

function LoginRoute() {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) return <Navigate to="/" replace />
  return <LoginPage />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route path="/forgot-password" element={<ForgotPasswordStub />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardShell />}>
          <Route index element={<Navigate to="/leads" replace />} />
          <Route path="/leads" element={<LeadsListPage />} />
          <Route path="/leads/:id" element={<LeadDetailPage />} />
          <Route path="/opportunities" element={<KanbanPage />} />
          <Route path="/accounts" element={<AccountsListPage />} />
          <Route path="/accounts/:id" element={<Account360Page />} />
          <Route path="/contacts" element={<ContactsListPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
