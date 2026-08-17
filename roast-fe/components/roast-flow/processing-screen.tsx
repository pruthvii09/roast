"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { CheckCircle2, RotateCcw, TriangleAlert } from "lucide-react"

import { RoastScoreDial } from "@/components/marketing/roast-score-dial"
import {
  INTENSITY_OPTIONS,
  LANGUAGE_OPTIONS,
  NUCLEAR_WARNING,
  PROCESSING_FINAL_STRETCH_MESSAGES,
  PROCESSING_MESSAGES,
  PROCESSING_OPENING_MESSAGE,
  SUBMISSION_TYPE_OPTIONS,
} from "@/components/roast-flow/copy"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Progress, ProgressIndicator, ProgressTrack } from "@/components/ui/progress"
import { getApiErrorMessage } from "@/lib/api/form-errors"
import { useCreateRoastRunMutation, useRoastRunQuery, useRoastRunStatusQuery } from "@/lib/api/roasts/queries"
import type { Intensity, Language, RoastRun, Submission } from "@/lib/api/types"
import { cn } from "@/lib/utils"

const MESSAGE_INTERVAL_MS = 2600
const FINAL_STRETCH_INTERVAL_MS = 4200
/** Delay before revealing the completed state — a beat so it reads as a reveal, not an abrupt swap. */
const COMPLETION_REVEAL_DELAY_MS = 450

interface ProcessingScreenProps {
  submission: Submission
  language: Language
  intensity: Intensity
  roastRun: RoastRun
  onDone: () => void
}

function ProcessingScreen({ submission, language, intensity, roastRun, onDone }: ProcessingScreenProps) {
  const router = useRouter()
  const [activeRun, setActiveRun] = useState<RoastRun>(roastRun)
  const [messageIndex, setMessageIndex] = useState(0)
  const [showResult, setShowResult] = useState(false)
  const retryRoast = useCreateRoastRunMutation(submission.id)

  const statusQuery = useRoastRunStatusQuery(activeRun.id, true)
  const status = statusQuery.data?.status ?? activeRun.status
  const errorMessage = statusQuery.data?.error_message || activeRun.error_message
  const isTerminal = status === "completed" || status === "failed"

  const detailQuery = useRoastRunQuery(activeRun.id, status === "completed")

  const typeOption = SUBMISSION_TYPE_OPTIONS.find((o) => o.value === submission.submission_type)
  const languageOption = LANGUAGE_OPTIONS.find((o) => o.value === language)
  const intensityOption = INTENSITY_OPTIONS.find((o) => o.value === intensity)
  const IntensityIcon = intensityOption?.icon

  const submissionLabel =
    submission.submission_type === "resume"
      ? submission.assets[0]?.original_filename || submission.title || "Resume"
      : submission.source_url || submission.title || "—"

  const messages = [PROCESSING_OPENING_MESSAGE[submission.submission_type], ...PROCESSING_MESSAGES]

  // Rotates the playful status line while the run is in flight. Purely
  // decorative UI copy — once the scripted sequence runs out, it cycles a
  // small "taking a bit longer" pool instead of restarting from the
  // opening line, which would wrongly imply work had restarted.
  useEffect(() => {
    if (isTerminal) return
    const inFinalStretch = messageIndex >= messages.length - 1
    const timer = setTimeout(
      () => setMessageIndex((i) => i + 1),
      inFinalStretch ? FINAL_STRETCH_INTERVAL_MS : MESSAGE_INTERVAL_MS
    )
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messageIndex, isTerminal])

  const currentMessage =
    messageIndex < messages.length
      ? messages[messageIndex]
      : PROCESSING_FINAL_STRETCH_MESSAGES[(messageIndex - messages.length) % PROCESSING_FINAL_STRETCH_MESSAGES.length]

  // The interval-based poll already skips its network request while the tab
  // is hidden (refetchIntervalInBackground: false) — this just catches up
  // immediately on return instead of waiting for the next scheduled tick.
  useEffect(() => {
    function handleVisibility() {
      if (document.visibilityState === "visible" && !isTerminal) {
        statusQuery.refetch()
      }
    }
    document.addEventListener("visibilitychange", handleVisibility)
    return () => document.removeEventListener("visibilitychange", handleVisibility)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isTerminal])

  useEffect(() => {
    if (status !== "completed") return
    const timer = setTimeout(() => setShowResult(true), COMPLETION_REVEAL_DELAY_MS)
    return () => clearTimeout(timer)
  }, [status])

  async function handleRetry() {
    try {
      const run = await retryRoast.mutateAsync({ language, intensity })
      setActiveRun(run)
      setMessageIndex(0)
      setShowResult(false)
    } catch {
      // surfaced below via retryRoast.isError
    }
  }

  function handleReturnToDashboard() {
    router.push("/dashboard")
    onDone()
  }

  function handleViewRoast() {
    router.push(`/roasts/${activeRun.id}`)
    onDone()
  }

  const heading =
    status === "completed"
      ? "Your roast is ready."
      : status === "failed"
        ? "Something went wrong."
        : "Cooking your roast…"

  return (
    <div className="relative space-y-6 overflow-hidden rounded-3xl border border-border bg-card px-5 py-7 sm:px-7">
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div
          className="absolute top-1/2 left-1/2 size-72 -translate-x-1/2 -translate-y-1/2 rounded-full blur-3xl motion-safe:animate-glow-drift"
          style={{
            background:
              status === "failed"
                ? "radial-gradient(circle, color-mix(in oklch, var(--destructive) 16%, transparent), transparent 70%)"
                : status === "completed"
                  ? "radial-gradient(circle, color-mix(in oklch, var(--success) 18%, transparent), transparent 70%)"
                  : "radial-gradient(circle, color-mix(in oklch, var(--primary) 16%, transparent), transparent 70%)",
          }}
        />
      </div>

      <div className="flex flex-col items-center gap-5 text-center">
        <div
          className={cn(
            "flex size-16 items-center justify-center rounded-full transition-colors duration-500",
            status === "completed"
              ? "bg-success/10 text-success"
              : status === "failed"
                ? "bg-destructive/10 text-destructive"
                : "bg-primary/10 text-primary"
          )}
        >
          {status === "completed" ? (
            <CheckCircle2 className="size-7" />
          ) : status === "failed" ? (
            <TriangleAlert className="size-7" />
          ) : (
            <span
              aria-hidden
              className="size-7 rounded-full border-2 border-current border-t-transparent motion-safe:animate-spin motion-reduce:animate-pulse"
            />
          )}
        </div>

        <div role="status" aria-live="polite" aria-atomic="true" className="space-y-1.5">
          <h2 className="font-display text-2xl font-medium text-foreground">{heading}</h2>
          {!isTerminal ? (
            <p
              aria-hidden
              key={currentMessage}
              className="text-sm text-muted-foreground transition-opacity duration-300 motion-reduce:transition-none"
            >
              {currentMessage}
            </p>
          ) : status === "completed" ? (
            <p className="text-sm text-muted-foreground">
              {detailQuery.data?.summary || "Head to My Roasts to see the full breakdown."}
            </p>
          ) : null}
        </div>

        {!isTerminal ? (
          <Progress value={null} aria-label="Generating your roast" className="w-full max-w-xs">
            <ProgressTrack>
              <ProgressIndicator className="h-full w-1/3 rounded-full motion-safe:animate-progress-sweep motion-reduce:w-2/5 motion-reduce:animate-none" />
            </ProgressTrack>
          </Progress>
        ) : null}

        <dl className="w-full space-y-2.5 rounded-2xl border border-border/70 bg-muted/30 p-4 text-left">
          <div className="flex items-center justify-between gap-4">
            <dt className="text-sm text-muted-foreground">{typeOption?.label ?? "Submission"}</dt>
            <dd className="flex min-w-0 items-center gap-1.5 text-sm font-medium text-foreground">
              {typeOption?.icon ? <typeOption.icon className="size-3.5 shrink-0" /> : null}
              <span className="truncate">{submissionLabel}</span>
            </dd>
          </div>
          <div className="flex items-center justify-between gap-4">
            <dt className="text-sm text-muted-foreground">Language</dt>
            <dd className="text-sm font-medium text-foreground">{languageOption?.label ?? language}</dd>
          </div>
          <div className="flex items-center justify-between gap-4">
            <dt className="text-sm text-muted-foreground">Intensity</dt>
            <dd>
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold",
                  intensityOption?.chipClass
                )}
              >
                {IntensityIcon ? <IntensityIcon className="size-3.5" /> : null}
                {intensityOption?.label ?? intensity}
              </span>
            </dd>
          </div>
        </dl>

        {intensity === "nuclear" ? (
          <p className="-mt-1 text-xs font-medium text-destructive">{NUCLEAR_WARNING}</p>
        ) : null}

        {status === "failed" ? (
          <div className="w-full space-y-4">
            <Alert variant="destructive" className="text-left">
              <TriangleAlert />
              <AlertTitle>What happened</AlertTitle>
              <AlertDescription>
                {errorMessage || "Roast generation failed. You can try again."}
              </AlertDescription>
            </Alert>
            {retryRoast.isError ? (
              <Alert variant="destructive" className="text-left">
                <AlertDescription>{getApiErrorMessage(retryRoast.error)}</AlertDescription>
              </Alert>
            ) : null}
            <div className="flex flex-col-reverse gap-2.5 sm:flex-row sm:justify-center">
              <Button type="button" variant="outline" className="rounded-full" onClick={handleReturnToDashboard}>
                Return to dashboard
              </Button>
              <Button
                type="button"
                className="rounded-full"
                onClick={handleRetry}
                disabled={retryRoast.isPending}
              >
                <RotateCcw className={retryRoast.isPending ? "animate-spin" : undefined} />
                Try again
              </Button>
            </div>
          </div>
        ) : null}

        {status === "completed" ? (
          <div
            className={cn(
              "w-full space-y-4 transition-all duration-500 motion-reduce:transition-none",
              showResult ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
            )}
          >
            {detailQuery.data?.score !== null && detailQuery.data?.score !== undefined ? (
              <div className="flex justify-center">
                <RoastScoreDial score={detailQuery.data.score} />
              </div>
            ) : null}
            {detailQuery.data?.final_verdict ? (
              <p className="text-sm text-balance text-muted-foreground italic">
                “{detailQuery.data.final_verdict}”
              </p>
            ) : null}
            <div className="flex flex-col-reverse gap-2.5 sm:flex-row sm:justify-center">
              <Button type="button" variant="outline" className="rounded-full" onClick={onDone}>
                Close
              </Button>
              <Button type="button" className="rounded-full" onClick={handleViewRoast}>
                View my roast
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

export { ProcessingScreen }
