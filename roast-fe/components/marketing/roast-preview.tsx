import { Eye } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"
import { RoastFindingList, type RoastFinding } from "./roast-finding-list"
import { RoastScoreDial } from "./roast-score-dial"

const FINDINGS: RoastFinding[] = [
  {
    icon: "🔥",
    title: "The Corporate Word Salad",
    roast:
      "\"Synergized cross-functional deliverables\" — cool, but what did you actually do?",
    severity: "high",
  },
  {
    icon: "💀",
    title: "The \"Responsible for...\" Epidemic",
    roast:
      "Six bullet points, six \"responsible for\"s. Responsible for variety, maybe.",
    severity: "medium",
  },
  {
    icon: "⚠️",
    title: "Where Are The Actual Results?",
    roast:
      "Numbers exist. Use them. \"Improved performance\" improved it from what to what?",
    severity: "critical",
  },
]

function RoastPreview() {
  return (
    <div id="example-roast" className="scroll-mt-16">
      <Container className="pb-20 sm:pb-28 pt-10">
        <FadeIn>
          <Card className="mx-auto w-full max-w-2xl rounded-3xl border-none py-0 shadow-xl shadow-foreground/6 ring-1 ring-border">
            <CardHeader className="border-b border-border/70 py-4">
              <div className="flex items-center justify-between">
                <Badge
                  variant="secondary"
                  className="gap-1.5 rounded-full font-mono text-[0.65rem] tracking-wide uppercase"
                >
                  <Eye className="size-3" />
                  Example roast
                </Badge>
                <span className="font-mono text-[0.7rem] tracking-wide text-muted-foreground uppercase">
                  Resume · Brutal · English
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-5 py-5">
              <div className="flex items-center gap-4">
                <RoastScoreDial score={38} />
                <div className="space-y-1">
                  <p className="font-display text-lg text-foreground italic">
                    &quot;Technically a resume. Emotionally, a cry for
                    help.&quot;
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
    </div>
  )
}

export { RoastPreview }
