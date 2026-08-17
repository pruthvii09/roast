import { Feather, Flame, MessageSquareQuote, Skull } from "lucide-react"

import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"
import { cn } from "@/lib/utils"

const INTENSITIES = [
  {
    key: "gentle",
    label: "Gentle",
    tagline: "Constructive, encouraging, still honest.",
    icon: Feather,
    level: 1,
    tone: "text-muted-foreground",
  },
  {
    key: "sarcastic",
    label: "Sarcastic",
    tagline: "A raised eyebrow in text form.",
    icon: MessageSquareQuote,
    level: 2,
    tone: "text-foreground",
  },
  {
    key: "brutal",
    label: "Brutal",
    tagline: "No cushioning. Just the truth.",
    icon: Flame,
    level: 3,
    tone: "text-warning",
  },
  {
    key: "nuclear",
    label: "Nuclear",
    tagline: "Read at your own risk.",
    icon: Skull,
    level: 4,
    tone: "text-destructive",
  },
] as const

function RoastStyles() {
  return (
    <Container className="py-20 sm:py-28">
      <FadeIn className="mx-auto mb-12 max-w-xl text-center">
        <p className="mb-3 font-mono text-xs tracking-widest text-primary uppercase">
          Intensity
        </p>
        <h2 className="font-display text-3xl font-medium text-foreground sm:text-4xl">
          Choose your damage
        </h2>
        <p className="mt-3 text-muted-foreground">
          Four intensities. All of them honest.
        </p>
      </FadeIn>
      <FadeIn className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {INTENSITIES.map(({ key, label, tagline, icon: Icon, level, tone }) => (
          <div
            key={key}
            className="group rounded-2xl border border-border bg-card p-5 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-foreground/4"
          >
            <Icon className={cn("size-5", tone)} strokeWidth={2} />
            <h3 className="mt-4 text-base font-semibold text-foreground">
              {label}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">{tagline}</p>
            <div className="mt-4 flex gap-1">
              {[1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  className={cn(
                    "h-1.5 flex-1 rounded-full",
                    i <= level ? "bg-primary" : "bg-muted"
                  )}
                />
              ))}
            </div>
          </div>
        ))}
      </FadeIn>
    </Container>
  )
}

export { RoastStyles }
