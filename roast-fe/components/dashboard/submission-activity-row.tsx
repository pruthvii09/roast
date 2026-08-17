"use client"

import { useState } from "react"
import Link from "next/link"
import { ChevronDown, FileText, GitBranch, Globe } from "lucide-react"

import { CreateRoastControl } from "@/components/dashboard/create-roast-control"
import { RoastStatusBadge } from "@/components/dashboard/roast-status-badge"
import { SubmissionStatusBadge } from "@/components/dashboard/submission-status-badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useRoastRunsForSubmissionQuery } from "@/lib/api/roasts/queries"
import type { SubmissionList } from "@/lib/api/types"
import { cn } from "@/lib/utils"

const TYPE_ICON = { resume: FileText, website: Globe, github: GitBranch } as const

const LANGUAGE_LABEL: Record<string, string> = {
  en: "English",
  hi: "Hindi",
  hinglish: "Hinglish",
}

const INTENSITY_LABEL: Record<string, string> = {
  gentle: "Gentle",
  sarcastic: "Sarcastic",
  brutal: "Brutal",
  nuclear: "Nuclear",
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

function SubmissionActivityRow({ submission }: { submission: SubmissionList }) {
  const [expanded, setExpanded] = useState(false)
  const roastsQuery = useRoastRunsForSubmissionQuery(submission.id, expanded)
  const Icon = TYPE_ICON[submission.submission_type]

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/40"
      >
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium text-foreground">
            {submission.title || `Untitled ${submission.submission_type}`}
          </span>
          <span className="block text-xs text-muted-foreground capitalize">
            {submission.submission_type} · {formatDate(submission.created_at)}
          </span>
        </span>
        <SubmissionStatusBadge status={submission.status} />
        <ChevronDown
          className={cn(
            "size-4 shrink-0 text-muted-foreground transition-transform",
            expanded && "rotate-180"
          )}
        />
      </button>

      {expanded ? (
        <div className="space-y-2 border-t border-border px-4 py-3">
          {submission.status === "failed" ? (
            <p className="text-sm text-destructive">
              {submission.error_message || "Extraction failed for this submission."}
            </p>
          ) : submission.status === "processing" || submission.status === "draft" ? (
            <p className="text-sm text-muted-foreground">
              Still processing — check back in a moment.
            </p>
          ) : roastsQuery.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : roastsQuery.isError ? (
            <p className="text-sm text-destructive">Couldn&apos;t load roasts for this submission.</p>
          ) : (
            <>
              {(roastsQuery.data ?? []).map((run) => (
                <Link
                  key={run.id}
                  href={`/roasts/${run.id}`}
                  className="flex flex-wrap items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 text-sm transition-colors hover:bg-muted"
                >
                  <span className="font-medium text-foreground">
                    {LANGUAGE_LABEL[run.language]}
                  </span>
                  <span className="text-muted-foreground">·</span>
                  <span className="text-muted-foreground">{INTENSITY_LABEL[run.intensity]}</span>
                  <RoastStatusBadge status={run.status} />
                  {run.score !== null ? (
                    <span className="ml-auto font-mono text-xs text-muted-foreground">
                      Score {run.score}
                    </span>
                  ) : null}
                </Link>
              ))}
              <CreateRoastControl submissionId={submission.id} />
            </>
          )}
        </div>
      ) : null}
    </div>
  )
}

export { SubmissionActivityRow }
