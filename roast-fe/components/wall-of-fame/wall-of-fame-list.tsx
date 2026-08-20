"use client"

import { Trophy } from "lucide-react"

import { WallOfFameCard } from "@/components/wall-of-fame/wall-of-fame-card"
import { EmptyState } from "@/components/shared/empty-state"
import { ErrorState } from "@/components/shared/error-state"
import { CardSkeleton } from "@/components/shared/loading-skeletons"
import { useWallOfFameQuery } from "@/lib/api/shares/queries"

function WallOfFameList() {
  const query = useWallOfFameQuery({ page_size: 24 })

  if (query.isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <CardSkeleton key={index} />
        ))}
      </div>
    )
  }

  if (query.isError) {
    return (
      <ErrorState
        description="We couldn't load the Wall of Fame. Check your connection and try again."
        onRetry={() => query.refetch()}
      />
    )
  }

  const entries = query.data ?? []

  if (entries.length === 0) {
    return (
      <EmptyState
        icon={Trophy}
        title="No roasts featured yet."
        description="Owners can feature their roast from its share page — check back soon."
      />
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {entries.map((entry) => (
        <WallOfFameCard key={entry.token} entry={entry} />
      ))}
    </div>
  )
}

export { WallOfFameList }
