import { Badge } from "@/components/ui/badge"
import type { Severity } from "@/lib/api/types"

interface RoastFinding {
  icon: string
  title: string
  roast: string
  severity: Extract<Severity, "medium" | "high" | "critical">
}

function severityVariant(
  severity: RoastFinding["severity"]
): "warning" | "destructive" {
  return severity === "medium" ? "warning" : "destructive"
}

function RoastFindingList({ findings }: { findings: RoastFinding[] }) {
  return (
    <ul className="space-y-1">
      {findings.map((finding) => (
        <li
          key={finding.title}
          className="flex items-start gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/60"
        >
          <span
            className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-base leading-none"
            aria-hidden
          >
            {finding.icon}
          </span>
          <div className="min-w-0 space-y-0.5">
            <p className="text-sm font-medium text-foreground">
              {finding.title}
            </p>
            <p className="text-sm text-muted-foreground">{finding.roast}</p>
          </div>
          <Badge
            variant={severityVariant(finding.severity)}
            className="ml-auto shrink-0 rounded-full font-mono text-[0.65rem] tracking-wide uppercase"
          >
            {finding.severity}
          </Badge>
        </li>
      ))}
    </ul>
  )
}

export { RoastFindingList, type RoastFinding }
