import Link from "next/link"
import { ArrowRight } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"

function FinalCta() {
  return (
    <Container className="py-20 sm:py-28">
      <FadeIn className="relative mx-auto flex max-w-2xl flex-col items-center gap-5 overflow-hidden rounded-3xl border border-border bg-card px-6 py-16 text-center sm:px-12">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10"
        >
          <div className="absolute top-1/2 left-1/2 h-[26rem] w-[26rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(closest-side,color-mix(in_oklch,var(--primary)_10%,transparent),transparent)] blur-3xl" />
        </div>
        <p className="font-mono text-xs tracking-widest text-primary uppercase">
          No more guessing
        </p>
        <h2 className="font-display text-3xl font-medium text-foreground sm:text-4xl">
          Ready to hear the truth?
        </h2>
        <p className="text-muted-foreground">
          It takes two minutes. The feedback lasts a career.
        </p>
        <Button
          render={<Link href="/register" />}
          nativeButton={false}
          size="lg"
          className="w-full rounded-full px-6 shadow-sm sm:w-auto"
        >
          Roast Mine
          <ArrowRight />
        </Button>
      </FadeIn>
    </Container>
  )
}

export { FinalCta }
