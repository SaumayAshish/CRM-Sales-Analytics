// Reused across Lead detail and Account 360 (FR-25, FR-53). System-
// generated entries (logged_by === null, per FR-54) render with a
// distinct "System" marker rather than a blank actor.
import { formatDistanceToNow } from "date-fns"
import { Bot, Calendar, CheckCircle2, Mail, MessageSquare, Phone, RefreshCw } from "lucide-react"

import { EmptyState } from "@/components/shared/EmptyState"
import { Skeleton } from "@/components/ui/skeleton"
import { useActivityTypes } from "@/hooks/useLookups"
import type { Activity } from "@/types"

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Call: Phone,
  Email: Mail,
  Meeting: Calendar,
  Task: CheckCircle2,
  Note: MessageSquare,
  "Status Change": RefreshCw,
}

interface ActivityTimelineProps {
  activities: Activity[] | undefined
  isLoading?: boolean
}

export function ActivityTimeline({ activities, isLoading }: ActivityTimelineProps) {
  const { data: activityTypes } = useActivityTypes()

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    )
  }

  if (!activities || activities.length === 0) {
    return <EmptyState message="No activity yet." />
  }

  const typeNameById = new Map(activityTypes?.map((t) => [t.id, t.name]) ?? [])

  return (
    <ol className="space-y-4 border-l pl-4">
      {activities.map((activity) => {
        const typeName = typeNameById.get(activity.type_id) ?? "Activity"
        const Icon = ICONS[typeName] ?? MessageSquare
        const isSystem = activity.logged_by === null

        return (
          <li key={activity.id} className="relative">
            <span className="absolute -left-[22px] flex size-6 items-center justify-center rounded-full border bg-background">
              {isSystem ? <Bot className="size-3.5 text-muted-foreground" /> : <Icon className="size-3.5" />}
            </span>
            <div className="rounded-md border p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium">
                  {typeName} {isSystem && <span className="text-xs font-normal text-muted-foreground">(System)</span>}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                </span>
              </div>
              {activity.notes && <p className="mt-1 text-sm text-muted-foreground">{activity.notes}</p>}
              {activity.due_at && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Due {new Date(activity.due_at).toLocaleDateString()}
                  {!activity.is_complete && new Date(activity.due_at) < new Date() && (
                    <span className="ml-2 font-medium text-destructive">Overdue</span>
                  )}
                </p>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
