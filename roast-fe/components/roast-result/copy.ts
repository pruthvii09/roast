import { AlertOctagon, Flame, Info, MessageCircleWarning, Skull } from "lucide-react"

import type { Severity } from "@/lib/api/types"

/**
 * Per-finding severity presentation — deliberately escalates using only the
 * existing design-system tokens (muted/secondary/warning/destructive), never
 * a new hue. The "eyebrow" label is decorative UI copy, not backend data —
 * `category` (free text from the AI) is shown separately, smaller.
 */
export const SEVERITY_CONFIG: Record<
  Severity,
  {
    eyebrow: string
    icon: typeof Info
    badgeVariant: "secondary" | "outline" | "warning" | "destructive"
    tone: string
  }
> = {
  info: {
    eyebrow: "Noted",
    icon: Info,
    badgeVariant: "secondary",
    tone: "text-muted-foreground",
  },
  low: {
    eyebrow: "Minor Slip",
    icon: MessageCircleWarning,
    badgeVariant: "outline",
    tone: "text-foreground",
  },
  medium: {
    eyebrow: "Questionable Choice",
    icon: AlertOctagon,
    badgeVariant: "warning",
    tone: "text-warning",
  },
  high: {
    eyebrow: "The Crime",
    icon: Flame,
    badgeVariant: "destructive",
    tone: "text-destructive",
  },
  critical: {
    eyebrow: "Capital Offense",
    icon: Skull,
    badgeVariant: "destructive",
    tone: "text-destructive",
  },
}
