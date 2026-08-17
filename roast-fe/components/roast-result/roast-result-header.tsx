import { RoastScoreDial } from "@/components/marketing/roast-score-dial"
import { INTENSITY_OPTIONS, LANGUAGE_OPTIONS, SUBMISSION_TYPE_OPTIONS } from "@/components/roast-flow/copy"
import type { RoastRun, Submission } from "@/lib/api/types"
import { cn } from "@/lib/utils"

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

interface RoastResultHeaderProps {
  roastRun: RoastRun
  submission: Submission
}

function RoastResultHeader({ roastRun, submission }: RoastResultHeaderProps) {
  const typeOption = SUBMISSION_TYPE_OPTIONS.find((o) => o.value === submission.submission_type)
  const languageOption = LANGUAGE_OPTIONS.find((o) => o.value === roastRun.language)
  const intensityOption = INTENSITY_OPTIONS.find((o) => o.value === roastRun.intensity)
  const TypeIcon = typeOption?.icon
  const IntensityIcon = intensityOption?.icon

  const submissionLabel =
    submission.submission_type === "resume"
      ? submission.assets[0]?.original_filename || submission.title || "Resume"
      : submission.source_url || submission.title || "—"

  // Reflects intensity subtly (same tokens as everywhere else) — never a new hue.
  const scoreTone = roastRun.intensity === "nuclear" ? "destructive" : roastRun.intensity === "brutal" ? "warning" : "primary"

  return (
    <header className="relative overflow-hidden rounded-3xl border border-border/70 px-5 py-8 sm:px-8 sm:py-10">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div
          className="absolute top-0 left-1/2 size-80 -translate-x-1/2 -translate-y-1/3 rounded-full blur-3xl"
          style={{
            background: `radial-gradient(circle, color-mix(in oklch, var(--${scoreTone}) 14%, transparent), transparent 70%)`,
          }}
        />
      </div>

      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5 text-sm text-muted-foreground">
        {TypeIcon ? <TypeIcon className="size-4 shrink-0" /> : null}
        <span className="min-w-0 max-w-[16rem] truncate font-medium text-foreground">{submissionLabel}</span>
        <span aria-hidden>·</span>
        <span>{languageOption?.label ?? roastRun.language}</span>
        <span aria-hidden>·</span>
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold",
            intensityOption?.chipClass
          )}
        >
          {IntensityIcon ? <IntensityIcon className="size-3" /> : null}
          {intensityOption?.label ?? roastRun.intensity}
        </span>
        <span aria-hidden>·</span>
        <time dateTime={roastRun.created_at}>{formatDate(roastRun.created_at)}</time>
      </div>

      <div className="mt-6 flex flex-col items-center gap-4 text-center sm:flex-row sm:items-center sm:text-left">
        {roastRun.score !== null ? (
          <RoastScoreDial score={roastRun.score} size={104} tone={scoreTone} />
        ) : null}
        <p className="font-display text-2xl leading-tight font-medium text-balance text-foreground sm:text-3xl">
          &ldquo;{roastRun.final_verdict}&rdquo;
        </p>
      </div>
    </header>
  )
}

export { RoastResultHeader }
