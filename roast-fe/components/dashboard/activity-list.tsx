"use client"

import { Flame } from "lucide-react"

import { useNewRoast } from "@/components/app-shell/new-roast-context"
import { SubmissionActivityRow } from "@/components/dashboard/submission-activity-row"
import { EmptyState } from "@/components/shared/empty-state"
import { ErrorState } from "@/components/shared/error-state"
import { ListSkeleton } from "@/components/shared/loading-skeletons"
import { useSubmissionsQuery } from "@/lib/api/submissions/queries"

function ActivityList({ pageSize }: { pageSize: number }) {
  const { open } = useNewRoast()
  const query = useSubmissionsQuery({ page_size: pageSize })

  if (query.isLoading) {
    return <ListSkeleton rows={Math.min(pageSize, 3)} />
  }

  if (query.isError) {
    return (
      <ErrorState
        description="We couldn't load your roasts. Check your connection and try again."
        onRetry={() => query.refetch()}
      />
    )
  }

  const submissions = query.data ?? []

  if (submissions.length === 0) {
    return (
      <EmptyState
        icon={Flame}
        title="Nothing roasted yet."
        description="Submit a resume, website, or GitHub profile to get started."
        action={{ label: "Roast your first thing", onClick: () => open() }}
      />
    )
  }

  return (
    <div className="space-y-2">
      {submissions.map((submission) => (
        <SubmissionActivityRow key={submission.id} submission={submission} />
      ))}
    </div>
  )
}

export { ActivityList }
