"use client"

import { Check } from "lucide-react"
import type { ReactNode } from "react"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const DEFAULT_ACTIVE_CLASSNAME = "border-primary/40 bg-primary/[0.03] ring-1 ring-primary/20"
const DEFAULT_ACTIVE_INDICATOR_CLASSNAME = "border-primary bg-primary text-primary-foreground"

interface SelectableCardProps {
  name: string
  value: string
  checked: boolean
  onChange: (value: string) => void
  children: ReactNode
  className?: string
  /** Checked-state border/ring/background — defaults to a primary tint. Lets a caller (e.g. intensity selection) accent each option with its own tone instead of one flat color for every option. */
  activeClassName?: string
  /** Checked-state indicator-circle border/background — defaults to primary, same override reasoning as activeClassName. */
  activeIndicatorClassName?: string
  /** Renders the card unselectable with a "Coming soon" badge, for an option that's visible but not yet available rather than removed outright. */
  comingSoon?: boolean
}

/**
 * A real <input type="radio"> visually hidden under a styled label — gives
 * native keyboard (arrow-key roving, Tab, Space) and screen-reader radio
 * semantics for free instead of reimplementing ARIA roving-tabindex by hand.
 */
function SelectableCard({
  name,
  value,
  checked,
  onChange,
  children,
  className,
  activeClassName = DEFAULT_ACTIVE_CLASSNAME,
  activeIndicatorClassName = DEFAULT_ACTIVE_INDICATOR_CLASSNAME,
  comingSoon = false,
}: SelectableCardProps) {
  return (
    <label
      className={cn(
        "group relative flex flex-col rounded-2xl border border-border bg-card p-5 transition-all has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-ring/50",
        comingSoon
          ? "cursor-not-allowed opacity-60"
          : "cursor-pointer hover:-translate-y-0.5 hover:shadow-lg hover:shadow-foreground/4",
        checked && activeClassName,
        className
      )}
    >
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        disabled={comingSoon}
        onChange={() => onChange(value)}
        className="sr-only"
      />
      {comingSoon ? (
        <Badge variant="secondary" className="absolute top-4 right-4">
          Coming soon
        </Badge>
      ) : (
        <span
          aria-hidden
          className={cn(
            "absolute top-4 right-4 flex size-5 items-center justify-center rounded-full border transition-all",
            checked ? activeIndicatorClassName : "border-border bg-transparent text-transparent"
          )}
        >
          <Check className="size-3" />
        </span>
      )}
      {children}
    </label>
  )
}

export { SelectableCard }
