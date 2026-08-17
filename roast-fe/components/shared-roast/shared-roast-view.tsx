"use client"

import { FindingsList } from "@/components/roast-result/findings-list"
import { OpeningRoast } from "@/components/roast-result/opening-roast"
import { RoastResultSkeleton } from "@/components/roast-result/roast-result-skeleton"
import { RoastSections } from "@/components/roast-result/roast-sections"
import { ReactionBar } from "@/components/shared-roast/reaction-bar"
import { SharedRoastHeader } from "@/components/shared-roast/shared-roast-header"
import { ErrorState } from "@/components/shared/error-state"
import { FadeIn } from "@/components/shared/fade-in"
import { isApiError } from "@/lib/api/errors"
import { usePublicRoastQuery } from "@/lib/api/shares/queries"

// Same reveal sequencing as components/roast-result/roast-result.tsx — see
// its comment for why (independent call site reusing the same leaf
// components, kept in sync as a value, not shared logic).
const HEADER_REVEAL_DELAY_MS = 0
const OPENING_REVEAL_DELAY_MS = 150
const FINDINGS_BASE_DELAY_MS = 300
const SECTIONS_REVEAL_DELAY_MS = 100
const ACTIONS_REVEAL_DELAY_MS = 100

/**
 * A revoked link, one that never existed, and one whose submission was
 * later deleted all 404 identically from the backend (see
 * apps.sharing.selectors.get_active_share_link_by_token) — this never
 * tries to distinguish those cases either.
 */
function SharedRoastView({ token }: { token: string }) {
  const query = usePublicRoastQuery(token)

  if (query.isLoading) {
    return <RoastResultSkeleton />
  }

  if (query.isError) {
    if (isApiError(query.error) && query.error.code === "NOT_FOUND") {
      return (
        <ErrorState
          title="This roast isn't available"
          description="The link may have been revoked, or it never existed."
        />
      )
    }
    return (
      <ErrorState
        description="We couldn't load this roast. Check your connection and try again."
        onRetry={() => query.refetch()}
      />
    )
  }

  const roast = query.data
  if (!roast) return null

  return (
    <div className="space-y-10 sm:space-y-14">
      <FadeIn delay={HEADER_REVEAL_DELAY_MS}>
        <SharedRoastHeader roast={roast} />
      </FadeIn>
      <OpeningRoast summary={roast.summary} delay={OPENING_REVEAL_DELAY_MS} />
      <FindingsList findings={roast.findings} baseDelay={FINDINGS_BASE_DELAY_MS} />
      <RoastSections sections={roast.sections} delay={SECTIONS_REVEAL_DELAY_MS} />
      <FadeIn delay={ACTIONS_REVEAL_DELAY_MS}>
        <ReactionBar token={token} reactions={roast.reactions} />
      </FadeIn>
    </div>
  )
}

export { SharedRoastView }
