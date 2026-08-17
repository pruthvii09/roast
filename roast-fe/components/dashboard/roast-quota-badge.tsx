"use client"

import { Sparkles } from "lucide-react"

import { useRoastQuotaQuery } from "@/lib/api/roasts/queries"

function RoastQuotaBadge() {
  const { data, isLoading, isError } = useRoastQuotaQuery()

  if (isLoading || isError || !data) return null

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground">
      <Sparkles className="size-3.5 text-primary" />
      {data.remaining} of {data.limit} roasts left this week
    </span>
  )
}

export { RoastQuotaBadge }
