import Link from "next/link"
import { Eye, Flame } from "lucide-react"

import { RoastScoreDial } from "@/components/marketing/roast-score-dial"
import { SUBMISSION_TYPE_OPTIONS } from "@/components/roast-flow/copy"
import { Card } from "@/components/ui/card"
import type { WallOfFameEntry } from "@/lib/api/types"

function WallOfFameCard({ entry }: { entry: WallOfFameEntry }) {
  const typeOption = SUBMISSION_TYPE_OPTIONS.find((o) => o.value === entry.submission.submission_type)
  const TypeIcon = typeOption?.icon ?? Flame
  const title = entry.submission.title || typeOption?.label || "Untitled"

  return (
    <Link href={`/r/${entry.token}`} className="block">
      <Card className="h-full transition-colors hover:bg-muted/40">
        <div className="flex items-start gap-3 px-(--card-spacing)">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <TypeIcon className="size-4" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-foreground">{title}</p>
            <p className="text-xs text-muted-foreground capitalize">
              {entry.submission.submission_type} · {entry.intensity}
            </p>
          </div>
          {entry.score !== null ? <RoastScoreDial score={entry.score} size={40} /> : null}
        </div>

        <p className="px-(--card-spacing) text-sm text-balance text-foreground">
          &ldquo;{entry.final_verdict || entry.summary}&rdquo;
        </p>

        <div className="mt-auto flex items-center gap-3 px-(--card-spacing) text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Flame className="size-3.5" aria-hidden />
            {entry.total_reactions} reaction{entry.total_reactions === 1 ? "" : "s"}
          </span>
          <span className="inline-flex items-center gap-1">
            <Eye className="size-3.5" aria-hidden />
            {entry.view_count}
          </span>
        </div>
      </Card>
    </Link>
  )
}

export { WallOfFameCard }
