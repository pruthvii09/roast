import { FindingCard } from "@/components/roast-result/finding-card"
import { FadeIn } from "@/components/shared/fade-in"
import type { RoastFinding } from "@/lib/api/types"

/** See finding-card.tsx's FindingCardFinding — same reuse-across-public-page reasoning. */
type ListedFinding = Pick<
  RoastFinding,
  "id" | "category" | "severity" | "title" | "roast_text" | "actual_feedback" | "position"
>

const FINDING_CARD_STAGGER_MS = 90
/** Caps added stagger at 4 cards (360ms) — cards past this reveal on their own scroll-trigger anyway. */
const MAX_STAGGERED_CARDS = 4

function FindingsList({
  findings,
  baseDelay = 0,
}: {
  findings: ListedFinding[]
  baseDelay?: number
}) {
  if (findings.length === 0) return null

  const sorted = [...findings].sort((a, b) => a.position - b.position)

  return (
    <section aria-labelledby="findings-heading" className="space-y-4">
      <FadeIn delay={baseDelay}>
        <h2
          id="findings-heading"
          className="font-mono text-xs font-semibold tracking-widest text-muted-foreground uppercase"
        >
          The Findings
        </h2>
      </FadeIn>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {sorted.map((finding, index) => (
          <FindingCard
            key={finding.id}
            finding={finding}
            delay={baseDelay + Math.min(index, MAX_STAGGERED_CARDS) * FINDING_CARD_STAGGER_MS}
          />
        ))}
      </div>
    </section>
  )
}

export { FindingsList }
