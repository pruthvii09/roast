import Link from "next/link"
import { ArrowRight, Sparkles } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"

function Hero() {
  return (
    <section className="relative overflow-x-hidden border-b border-border">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,var(--border)_1px,transparent_0)] bg-size-[32px_32px] opacity-60 [mask-image:radial-gradient(ellipse_60%_60%_at_50%_0%,black_30%,transparent_80%)]" />
        <div className="absolute top-[-16rem] left-1/2 h-[36rem] w-[50rem] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,color-mix(in_oklch,var(--primary)_14%,transparent),transparent)] blur-3xl motion-safe:animate-glow-drift" />
        <div className="absolute inset-y-0 left-[10%] hidden w-px bg-[linear-gradient(to_bottom,transparent,var(--border)_15%,var(--border)_85%,transparent)] lg:block" />
        <div className="absolute inset-y-0 right-[10%] hidden w-px bg-[linear-gradient(to_bottom,transparent,var(--border)_15%,var(--border)_85%,transparent)] lg:block" />
      </div>

      <Container className="flex flex-col items-center gap-7 py-24 text-center sm:py-32">
        <FadeIn>
          <Badge
            variant="outline"
            className="gap-1.5 rounded-full border-border bg-background/80 px-3 py-1 font-mono text-[0.7rem] tracking-wide text-muted-foreground uppercase backdrop-blur-sm"
          >
            <Sparkles className="size-3 text-primary" />
            AI-powered, brutally honest feedback
          </Badge>
        </FadeIn>
        <FadeIn delay={80}>
          <h1 className="max-w-3xl font-display text-5xl leading-[1.05] font-medium tracking-tight text-balance text-foreground sm:text-6xl md:text-7xl">
            Your resume deserves{" "}
            <span className="text-primary italic">the truth.</span>
          </h1>
        </FadeIn>
        <FadeIn delay={140}>
          <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
            Submit your resume, website, or GitHub profile. Get a roast that
            stings a little — and feedback you can actually use.
          </p>
        </FadeIn>
        <FadeIn
          delay={200}
          className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row"
        >
          <Button
            render={<Link href="/register" />}
            nativeButton={false}
            size="lg"
            className="w-full rounded-full px-6 shadow-sm sm:w-auto"
          >
            Roast Mine
            <ArrowRight />
          </Button>
          <Button
            render={<a href="#example-roast" />}
            nativeButton={false}
            variant="outline"
            size="lg"
            className="w-full rounded-full border-border bg-background px-6 sm:w-auto"
          >
            See an Example
          </Button>
        </FadeIn>
      </Container>
    </section>
  )
}

export { Hero }
