import { FileText, GitBranch, Globe } from "lucide-react"

import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"
import { cn } from "@/lib/utils"

const SUBMISSION_TYPES = [
  {
    icon: FileText,
    format: "PDF · DOCX",
    label: "Resume",
    description: "We'll read between every buzzworded line.",
  },
  {
    icon: Globe,
    format: "URL",
    label: "Website",
    description: "Portfolio, landing page, personal site — the whole thing.",
  },
  {
    icon: GitBranch,
    format: "PROFILE",
    label: "GitHub",
    description: "Pinned repos, README energy, commit history. Nowhere to hide.",
  },
] as const

function SubmissionTypes() {
  return (
    <Container className="py-20 sm:py-28">
      <FadeIn className="mx-auto mb-12 max-w-xl text-center">
        <p className="mb-3 font-mono text-xs tracking-widest text-primary uppercase">
          What you can submit
        </p>
        <h2 className="font-display text-3xl font-medium text-foreground sm:text-4xl">
          Roast anything you&apos;ve built
        </h2>
      </FadeIn>
      <FadeIn className="grid gap-4 sm:grid-cols-3">
        {SUBMISSION_TYPES.map(({ icon: Icon, format, label, description }, i) => (
          <div
            key={label}
            className={cn(
              "group relative overflow-hidden rounded-2xl border border-border bg-card p-6 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-foreground/4",
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
            <h3 className="mt-5 text-lg font-semibold text-foreground">
              {label}
            </h3>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {description}
            </p>
          </div>
        ))}
      </FadeIn>
    </Container>
  )
}

export { SubmissionTypes }
