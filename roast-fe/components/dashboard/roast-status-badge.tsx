import { CircleCheck, CircleX, Clock, Loader2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { ExtractionStatus } from "@/lib/api/types"

const CONFIG: Record<
  ExtractionStatus,
  { label: string; variant: "secondary" | "success" | "destructive" | "warning"; icon: typeof Clock }
> = {
  queued: { label: "Queued", variant: "secondary", icon: Clock },
  processing: { label: "Roasting…", variant: "warning", icon: Loader2 },
  completed: { label: "Completed", variant: "success", icon: CircleCheck },
  failed: { label: "Failed", variant: "destructive", icon: CircleX },
}

function RoastStatusBadge({ status }: { status: ExtractionStatus }) {
  const { label, variant, icon: Icon } = CONFIG[status]
  return (
    <Badge variant={variant} className="gap-1 rounded-full">
      <Icon className={Icon === Loader2 ? "size-3 animate-spin" : "size-3"} />
      {label}
    </Badge>
  )
}

export { RoastStatusBadge }
