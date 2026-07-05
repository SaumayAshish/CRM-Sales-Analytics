import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const SCORE_BAND_STYLES: Record<string, string> = {
  Hot: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  Warm: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  Cold: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
}

const STAGE_STYLES: Record<string, string> = {
  "Closed Won": "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  "Closed Lost": "bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
}
const DEFAULT_STAGE_STYLE = "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"

interface StatusBadgeProps {
  kind: "score_band" | "stage"
  value: string
  className?: string
}

export function StatusBadge({ kind, value, className }: StatusBadgeProps) {
  const style =
    kind === "score_band" ? SCORE_BAND_STYLES[value] : STAGE_STYLES[value] ?? DEFAULT_STAGE_STYLE

  return (
    <Badge variant="outline" className={cn("border-transparent font-medium", style, className)}>
      {value}
    </Badge>
  )
}
