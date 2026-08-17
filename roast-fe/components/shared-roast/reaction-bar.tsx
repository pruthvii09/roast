"use client"

import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import { useReactMutation } from "@/lib/api/shares/queries"
import type { ReactionTotals, ReactionType } from "@/lib/api/types"
import { cn } from "@/lib/utils"

const REACTIONS: { type: ReactionType; emoji: string; label: string }[] = [
  { type: "fire", emoji: "🔥", label: "Brutal" },
  { type: "skull", emoji: "💀", label: "Deceased" },
  { type: "laughing", emoji: "😂", label: "Painfully funny" },
  { type: "clap", emoji: "👏", label: "Fair" },
]

function storageKey(token: string): string {
  return `roast-anything:reacted:${token}`
}

interface ReactionBarProps {
  token: string
  reactions: ReactionTotals
}

/**
 * The POST always fires on click, even for a type already marked
 * "reacted" locally — there is no server-side per-visitor dedup (see
 * apps.sharing.models.Reaction's docstring), so the localStorage flag
 * below is a visual nicety only, never a request guard.
 */
function ReactionBar({ token, reactions }: ReactionBarProps) {
  const react = useReactMutation(token)
  const [reacted, setReacted] = useState<Set<ReactionType>>(new Set())

  useEffect(() => {
    // Must start empty on both server and first client render (localStorage
    // isn't readable during SSR) to avoid a hydration mismatch, so the real
    // value can only be applied after mount — the standard exception to
    // "don't setState synchronously in an effect".
    try {
      const stored = JSON.parse(localStorage.getItem(storageKey(token)) ?? "[]")
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setReacted(new Set(Array.isArray(stored) ? stored : []))
    } catch {
      // corrupt/blocked localStorage — fall back to no "already reacted" state
    }
  }, [token])

  function handleReact(type: ReactionType) {
    react.mutate({ reaction_type: type })
    setReacted((prev) => {
      const next = new Set(prev).add(type)
      try {
        localStorage.setItem(storageKey(token), JSON.stringify([...next]))
      } catch {
        // ignore — purely a UX nicety
      }
      return next
    })
  }

  return (
    <div className="flex flex-wrap items-center justify-center gap-2.5">
      {REACTIONS.map(({ type, emoji, label }) => (
        <Button
          key={type}
          type="button"
          variant="outline"
          className={cn("rounded-full", reacted.has(type) && "bg-muted text-foreground")}
          onClick={() => handleReact(type)}
          aria-label={label}
        >
          <span aria-hidden>{emoji}</span>
          {reactions[type]}
        </Button>
      ))}
    </div>
  )
}

export { ReactionBar }
