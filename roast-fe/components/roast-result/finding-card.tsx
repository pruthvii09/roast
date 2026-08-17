import { Badge } from "@/components/ui/badge"
import { SEVERITY_CONFIG } from "@/components/roast-result/copy"
import { FadeIn } from "@/components/shared/fade-in"
import type { RoastFinding } from "@/lib/api/types"
import { cn } from "@/lib/utils"

/**
 * Narrowed to the fields this component actually reads — a structural
 * subset both the owner-scoped RoastFinding and the public PublicRoastFinding
 * (apps.sharing's narrower payload) satisfy, so the public share page can
 * reuse this component unmodified.
 */
type FindingCardFinding = Pick<
  RoastFinding,
  "id" | "category" | "severity" | "title" | "roast_text" | "actual_feedback" | "position"
>

function FindingCard({ finding, delay = 0 }: { finding: FindingCardFinding; delay?: number }) {
  const config = SEVERITY_CONFIG[finding.severity]
  const Icon = config.icon

  return (
    <FadeIn delay={delay}>
      <article className="rounded-2xl border border-border bg-card p-5 shadow-sm shadow-foreground/[0.02] sm:p-6">
        <div className="flex items-center justify-between gap-3">
          <span
            className={cn(
              "inline-flex items-center gap-1.5 font-mono text-xs font-semibold tracking-wide uppercase",
              config.tone
            )}
          >
            <Icon className="size-3.5" aria-hidden />
            {config.eyebrow}
          </span>
          <Badge
            variant={config.badgeVariant}
            className="shrink-0 rounded-full font-mono text-[0.65rem] tracking-wide uppercase"
          >
            {finding.severity}
          </Badge>
        </div>

        <h3 className="mt-3 font-display text-lg font-semibold text-foreground">
          &ldquo;{finding.title}&rdquo;
        </h3>

        <p className="mt-2 text-lg leading-snug text-balance text-foreground/90 italic">
          {finding.roast_text}
        </p>

        {finding.actual_feedback ? (
          <div className="mt-4 border-t border-border/70 pt-3">
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              Actually useful
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{finding.actual_feedback}</p>
          </div>
        ) : null}
      </article>
    </FadeIn>
  )
}

export { FindingCard }
