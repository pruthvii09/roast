"use client"

import { FileText, GitBranch, Globe } from "lucide-react"

import { useNewRoast } from "@/components/app-shell/new-roast-context"
import type { SubmissionType } from "@/lib/api/types"
import { cn } from "@/lib/utils"

const OPTIONS: {
  type: SubmissionType
  icon: typeof FileText
  format: string
  label: string
  description: string
}[] = [
  {
    type: "resume",
    icon: FileText,
    format: "PDF · DOCX",
    label: "Resume",
    description: "We'll read between every buzzworded line.",
  },
  {
    type: "website",
    icon: Globe,
    format: "URL",
    label: "Website",
    description: "Portfolio, landing page, personal site — the whole thing.",
  },
  {
    type: "github",
    icon: GitBranch,
    format: "PROFILE",
    label: "GitHub",
    description: "Pinned repos, README energy, commit history. Nowhere to hide.",
  },
]

function NewRoastOptions() {
  const { open } = useNewRoast()

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {OPTIONS.map(({ type, icon: Icon, format, label, description }, i) => (
        <button
          key={type}
          type="button"
          onClick={() => open(type)}
          className={cn(
            "group relative overflow-hidden rounded-2xl border border-border bg-card p-6 text-left transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-foreground/4",
            i === 1 && "border-primary/30 ring-1 ring-primary/10"
          )}
        >
          <div className="flex items-center justify-between">
            <div className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Icon className="size-5" strokeWidth={2} />
            </div>
            <span className="font-mono text-[0.65rem] tracking-widest text-muted-foreground uppercase">
              {format}
            </span>
          </div>
          <h3 className="mt-5 text-lg font-semibold text-foreground">{label}</h3>
          <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
            Roast my {label.toLowerCase()} →
          </span>
        </button>
      ))}
    </div>
  )
}

export { NewRoastOptions }
