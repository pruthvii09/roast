import { cn } from "@/lib/utils"

interface RoastScoreDialProps {
  score: number
  /** Pixel size of the dial. Defaults to 64 (the compact inline usage). */
  size?: number
  /** Ring/text tone — lets callers reflect roast intensity without changing the design system. */
  tone?: "primary" | "warning" | "destructive"
}

const TONE_STROKE: Record<NonNullable<RoastScoreDialProps["tone"]>, string> = {
  primary: "stroke-primary",
  warning: "stroke-warning",
  destructive: "stroke-destructive",
}

function RoastScoreDial({ score, size = 64, tone = "primary" }: RoastScoreDialProps) {
  const radius = 26
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score / 100)
  const fontSize = Math.round(size * 0.28)

  return (
    <div
      className="relative flex shrink-0 items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg viewBox="0 0 64 64" className="-rotate-90" style={{ width: size, height: size }}>
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          strokeWidth="6"
          className="stroke-muted"
        />
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          strokeWidth="6"
          strokeLinecap="round"
          className={cn("transition-all duration-700", TONE_STROKE[tone])}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <span
        className="absolute font-semibold text-foreground tabular-nums"
        style={{ fontSize }}
      >
        {score}
      </span>
    </div>
  )
}

export { RoastScoreDial }
