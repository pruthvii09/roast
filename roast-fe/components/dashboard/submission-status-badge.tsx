import { CircleCheck, CircleX, Clock, Loader2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { SubmissionStatus } from "@/lib/api/types"

const CONFIG: Record<
  SubmissionStatus,
  { label: string; variant: "secondary" | "success" | "destructive" | "warning"; icon: typeof Clock }
> = {
  draft: { label: "Draft", variant: "secondary", icon: Clock },
  processing: { label: "Processing", variant: "warning", icon: Loader2 },
  ready: { label: "Ready", variant: "success", icon: CircleCheck },
  failed: { label: "Failed", variant: "destructive", icon: CircleX },
  deleted: { label: "Deleted", variant: "secondary", icon: CircleX },
}

function SubmissionStatusBadge({ status }: { status: SubmissionStatus }) {
  const { label, variant, icon: Icon } = CONFIG[status]
  return (
    <Badge variant={variant} className="gap-1 rounded-full">
      <Icon className={Icon === Loader2 ? "size-3 animate-spin" : "size-3"} />
      {label}
    </Badge>
  )
}

export { SubmissionStatusBadge }
