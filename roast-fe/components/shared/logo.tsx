import { Flame } from "lucide-react"

import { cn } from "@/lib/utils"

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 font-semibold tracking-tight", className)}>
      <Flame className="size-4 text-primary" strokeWidth={2.5} />
      Roast Anything
    </span>
  )
}
