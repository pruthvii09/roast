"use client"

import { useEffect, useRef, useState } from "react"
import { Loader2 } from "lucide-react"

import {
  INTENSITY_OPTIONS,
  LANGUAGE_OPTIONS,
  SUBMISSION_TYPE_OPTIONS,
} from "@/components/roast-flow/copy"
import { StepFooter } from "@/components/roast-flow/step-footer"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { getApiErrorMessage } from "@/lib/api/form-errors"
import { useSubmissionStatusQuery } from "@/lib/api/submissions/queries"
import { useCreateRoastRunMutation, useRoastQuotaQuery } from "@/lib/api/roasts/queries"
import type { Intensity, Language, RoastRun, Submission } from "@/lib/api/types"
import { cn } from "@/lib/utils"

interface StepReviewProps {
  submission: Submission
  language: Language
  intensity: Intensity
  onBack: () => void
  onRoastCreated: (roastRun: RoastRun) => void
}

function StepReview({ submission, language, intensity, onBack, onRoastCreated }: StepReviewProps) {
  const statusQuery = useSubmissionStatusQuery(submission.id, true)
  const currentStatus = statusQuery.data?.status ?? submission.status
  const createRoast = useCreateRoastRunMutation(submission.id)
  const quotaQuery = useRoastQuotaQuery()

  const [awaitingReady, setAwaitingReady] = useState(false)
  const [roastError, setRoastError] = useState<string | null>(null)
  const roastTriggeredRef = useRef(false)

  const typeOption = SUBMISSION_TYPE_OPTIONS.find((t) => t.value === submission.submission_type)
  const languageOption = LANGUAGE_OPTIONS.find((l) => l.value === language)
  const intensityOption = INTENSITY_OPTIONS.find((i) => i.value === intensity)
  const quotaExhausted = (quotaQuery.data?.remaining ?? 1) <= 0

  async function triggerRoast() {
    setRoastError(null)
    try {
      const run = await createRoast.mutateAsync({ language, intensity })
      onRoastCreated(run)
    } catch (error) {
      setRoastError(getApiErrorMessage(error))
    }
  }

  // Waits for extraction to finish before actually requesting the roast —
  // roastTriggeredRef guards this from ever firing more than once even if
  // the effect re-runs after currentStatus is already "ready".
  useEffect(() => {
    if (awaitingReady && currentStatus === "ready" && !roastTriggeredRef.current) {
      roastTriggeredRef.current = true
      triggerRoast()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [awaitingReady, currentStatus])

  function handleRoastIt() {
    if (currentStatus === "ready") {
      triggerRoast()
    } else if (currentStatus !== "failed") {
      setAwaitingReady(true)
    }
  }

  const summaryText =
    submission.submission_type === "resume"
      ? submission.assets[0]?.original_filename || submission.title || "Resume file"
      : submission.source_url || submission.title || "—"

  const isWaiting = awaitingReady && currentStatus !== "ready" && currentStatus !== "failed"

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Step 5</p>
        <h2 className="font-display text-2xl font-medium text-foreground">Ready to roast?</h2>
      </div>

      <dl className="space-y-3 rounded-2xl border border-border bg-card p-5">
        <ReviewRow
          label={typeOption?.label ?? "Submission"}
          value={summaryText}
          icon={typeOption?.icon}
        />
        <ReviewRow label="Language" value={languageOption?.label ?? language} />
        <ReviewRow
          label="Intensity"
          value={intensityOption?.label ?? intensity}
          icon={intensityOption?.icon}
          tone={intensityOption?.tone}
        />
      </dl>

      {currentStatus === "processing" || currentStatus === "draft" ? (
        <Alert>
          <AlertDescription>
            Still finishing up extraction — you can hit &quot;Roast It&quot; now and we&apos;ll
            start the moment it&apos;s ready.
          </AlertDescription>
        </Alert>
      ) : null}

      {currentStatus === "failed" ? (
        <Alert variant="destructive">
          <AlertDescription>
            {submission.error_message || "We couldn't process that submission."} Go back and try a
            different file or link.
          </AlertDescription>
        </Alert>
      ) : null}

      {roastError ? (
        <Alert variant="destructive">
          <AlertDescription>{roastError}</AlertDescription>
        </Alert>
      ) : null}

      {!roastError && quotaExhausted ? (
        <Alert variant="warning">
          <AlertDescription>
            You&apos;ve used all your roasts for this week. Check back later.
          </AlertDescription>
        </Alert>
      ) : null}

      <StepFooter
        onBack={onBack}
        onContinue={handleRoastIt}
        continueLabel={isWaiting ? "Waiting for extraction…" : "Roast It"}
        continueLoading={createRoast.isPending || isWaiting}
        continueDisabled={currentStatus === "failed" || quotaExhausted}
      />
    </div>
  )
}

function ReviewRow({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string
  value: string
  icon?: typeof Loader2
  tone?: string
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="flex min-w-0 items-center gap-1.5 text-sm font-medium text-foreground">
        {Icon ? <Icon className={cn("size-3.5 shrink-0", tone)} /> : null}
        <span className="truncate">{value}</span>
      </dd>
    </div>
  )
}

export { StepReview }
