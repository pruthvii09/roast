"use client"

import { useEffect, useState } from "react"
import { Sparkles, X } from "lucide-react"

import { useRoastQuotaQuery } from "@/lib/api/roasts/queries"

function dismissKey(expiresAt: string): string {
  return `roast-anything:bonus-banner-dismissed:${expiresAt}`
}

function daysLeft(expiresAt: string): number {
  const ms = new Date(expiresAt).getTime() - Date.now()
  return Math.max(1, Math.ceil(ms / (24 * 60 * 60 * 1000)))
}

/**
 * Reads the same GET /roasts/quota/ query RoastQuotaBadge already polls
 * (queryKeys.roasts.quota, deduped by TanStack Query) — no extra fetch.
 * Dismissal is scoped to the bonus's own expires_at, mirroring
 * ReactionBar's localStorage "already reacted" pattern, so re-dismissing
 * an unchanged bonus sticks for the session but a *new* bonus (a fresh
 * expires_at) reappears once.
 */
function ReferralBonusBanner() {
  const { data } = useRoastQuotaQuery()
  const bonusExpiresAt = data?.bonus_amount ? data.bonus_expires_at : null
  const [dismissed, setDismissed] = useState(true)

  useEffect(() => {
    let alreadyDismissed = false
    if (bonusExpiresAt) {
      try {
        alreadyDismissed = sessionStorage.getItem(dismissKey(bonusExpiresAt)) === "1"
      } catch {
        alreadyDismissed = false
      }
    }
    // Must start hidden on both server and first client render
    // (sessionStorage isn't readable during SSR) to avoid a hydration
    // mismatch — same reasoning as ReactionBar's "already reacted" state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDismissed(!bonusExpiresAt || alreadyDismissed)
  }, [bonusExpiresAt])

  if (!data?.bonus_amount || !bonusExpiresAt || dismissed) return null

  function handleDismiss() {
    try {
      sessionStorage.setItem(dismissKey(bonusExpiresAt as string), "1")
    } catch {
      // ignore — purely a UX nicety, never blocks dismissal
    }
    setDismissed(true)
  }

  const days = daysLeft(bonusExpiresAt)

  return (
    <div
      className="flex items-center justify-center gap-2 border-b border-border/70 px-4 py-2 text-sm"
      style={{
        background:
          "linear-gradient(90deg, color-mix(in oklch, var(--primary) 10%, transparent), color-mix(in oklch, var(--success) 12%, transparent))",
      }}
    >
      <Sparkles className="size-4 shrink-0 text-primary" aria-hidden />
      <p className="text-foreground">
        <span className="font-semibold">+{data.bonus_amount} bonus roasts</span> this week —{" "}
        {days} day{days === 1 ? "" : "s"} left
      </p>
      <button
        type="button"
        onClick={handleDismiss}
        aria-label="Dismiss"
        className="ml-1 shrink-0 rounded-full p-0.5 text-muted-foreground transition-colors hover:bg-foreground/10 hover:text-foreground"
      >
        <X className="size-3.5" />
      </button>
    </div>
  )
}

export { ReferralBonusBanner }
