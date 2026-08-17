"use client"

import { useEffect } from "react"

import { FindingsList } from "@/components/roast-result/findings-list"
import { OpeningRoast } from "@/components/roast-result/opening-roast"
import { RoastResultActions } from "@/components/roast-result/roast-result-actions"
import { RoastResultFailed } from "@/components/roast-result/roast-result-failed"
import { RoastResultHeader } from "@/components/roast-result/roast-result-header"
import { RoastResultPending } from "@/components/roast-result/roast-result-pending"
import { RoastResultSkeleton } from "@/components/roast-result/roast-result-skeleton"
import { RoastSections } from "@/components/roast-result/roast-sections"
import { FadeIn } from "@/components/shared/fade-in"
import { ErrorState } from "@/components/shared/error-state"
import { useRoastRunQuery, useRoastRunStatusQuery } from "@/lib/api/roasts/queries"
import { useSubmissionQuery } from "@/lib/api/submissions/queries"

// Sequences the reveal so the result reads as a reveal, not everything
// popping in at once — mirrors the "beat" processing-screen.tsx already
// uses for the hand-off into this page.
const HEADER_REVEAL_DELAY_MS = 0
const OPENING_REVEAL_DELAY_MS = 150
const FINDINGS_BASE_DELAY_MS = 300
const SECTIONS_REVEAL_DELAY_MS = 100
const ACTIONS_REVEAL_DELAY_MS = 100

/**
 * Full detail (useRoastRunQuery) is fetched once and NOT polled directly —
 * the lightweight status endpoint is what's meant for frequent polling
 * (see its own docstring). While the run is queued/processing, only the
 * status endpoint polls; the moment it goes terminal, this refetches the
 * full detail exactly once to pick up sections/findings/score.
 */
function RoastResult({ roastId }: { roastId: string }) {
  const roastQuery = useRoastRunQuery(roastId, true)
  const status = roastQuery.data?.status
  const isTerminal = status === "completed" || status === "failed"
  const statusQuery = useRoastRunStatusQuery(roastId, !!roastQuery.data && !isTerminal)
  const polledStatus = statusQuery.data?.status

  useEffect(() => {
    if (polledStatus === "completed" || polledStatus === "failed") {
      roastQuery.refetch()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [polledStatus])

  const roastRun = roastQuery.data
  const submissionQuery = useSubmissionQuery(roastRun?.submission ?? "", !!roastRun)

  if (roastQuery.isLoading) {
    return <RoastResultSkeleton />
  }

  if (roastQuery.isError) {
    return (
      <ErrorState
        description="We couldn't load this roast. Check your connection and try again."
        onRetry={() => roastQuery.refetch()}
      />
    )
  }

  if (!roastRun) return null

  if (roastRun.status === "queued" || roastRun.status === "processing") {
    return <RoastResultPending status={roastRun.status} />
  }

  if (submissionQuery.isLoading) {
    return <RoastResultSkeleton />
  }

  if (submissionQuery.isError) {
    return (
      <ErrorState
        description="We couldn't load the submission behind this roast."
        onRetry={() => submissionQuery.refetch()}
      />
    )
  }

  const submission = submissionQuery.data
  if (!submission) return null

  if (roastRun.status === "failed") {
    return <RoastResultFailed roastRun={roastRun} submission={submission} />
  }

  return (
    <div className="space-y-10 sm:space-y-14">
      <FadeIn delay={HEADER_REVEAL_DELAY_MS}>
        <RoastResultHeader roastRun={roastRun} submission={submission} />
      </FadeIn>
      <OpeningRoast summary={roastRun.summary} delay={OPENING_REVEAL_DELAY_MS} />
      <FindingsList findings={roastRun.findings} baseDelay={FINDINGS_BASE_DELAY_MS} />
      <RoastSections sections={roastRun.sections} delay={SECTIONS_REVEAL_DELAY_MS} />
      <FadeIn delay={ACTIONS_REVEAL_DELAY_MS}>
        <RoastResultActions roastRun={roastRun} submission={submission} />
      </FadeIn>
    </div>
  )
}

export { RoastResult }
