import { FlaskConical } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"
import { RoastFindingList, type RoastFinding } from "./roast-finding-list"
import { RoastScoreDial } from "./roast-score-dial"

const FINDINGS: RoastFinding[] = [
  {
    icon: "🎨",
    title: "The Portfolio That Loads Like It's 2009",
    roast:
      "Four fonts, a carousel, and an autoplay video. Bold choices for a design portfolio.",
    severity: "high",
  },
  {
    icon: "🧭",
    title: "Zero Navigation, Infinite Confidence",
    roast:
      "No nav bar, no footer, no way back to the homepage. Just vibes.",
    severity: "medium",
  },
  {
    icon: "📵",
    title: "The Contact Form That Contacts No One",
    roast: "It submits. It just doesn't go anywhere. Neither will this lead.",
    severity: "critical",
  },
]

function ExampleRoast() {
  return (
    <Container className="py-20 sm:py-28">
      <FadeIn className="mx-auto mb-12 max-w-xl text-center">
        <p className="mb-3 font-mono text-xs tracking-widest text-primary uppercase">
          Sample output
        </p>
        <h2 className="font-display text-3xl font-medium text-foreground sm:text-4xl">
          What a roast actually looks like
        </h2>
        <p className="mt-3 text-muted-foreground">
          Fictional submission, real format. No fake users, no fake numbers —
          just an honest preview of the output.
        </p>
      </FadeIn>
      <FadeIn>
        <Card className="mx-auto w-full max-w-2xl rounded-3xl border-none py-0 shadow-xl shadow-foreground/6 ring-1 ring-border">
          <CardHeader className="border-b border-border/70 py-4">
            <div className="flex items-center justify-between gap-3">
              <Badge
                variant="secondary"
                className="gap-1.5 rounded-full font-mono text-[0.65rem] tracking-wide uppercase"
              >
                <FlaskConical className="size-3" />
                Fictional roast
              </Badge>
              <span className="font-mono text-[0.7rem] tracking-wide text-muted-foreground uppercase">
                Website · Sarcastic · English
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 py-5">
            <div className="flex items-center gap-4">
              <RoastScoreDial score={54} />
              <div className="space-y-1">
                <p className="font-display text-lg text-foreground italic">
                  &quot;A beautiful site. Shame about the part where it
                  works.&quot;
                </p>
                <p className="font-mono text-xs tracking-wide text-muted-foreground uppercase">
                  3 findings · 1 critical
                </p>
              </div>
            </div>
            <Separator />
            <RoastFindingList findings={FINDINGS} />
          </CardContent>
        </Card>
      </FadeIn>
    </Container>
  )
}

export { ExampleRoast }
