import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"

const STEPS = [
  {
    n: "01",
    title: "Submit",
    body: "Upload your resume or drop a link to your site or GitHub profile.",
  },
  {
    n: "02",
    title: "Choose your roast",
    body: "Pick an intensity and a language. You're in control of the damage.",
  },
  {
    n: "03",
    title: "Get destroyed (constructively)",
    body: "Read the roast, then the actual feedback underneath it.",
  },
] as const

function HowItWorks() {
  return (
    <Container className="py-20 sm:py-28">
      <FadeIn className="mx-auto mb-14 max-w-xl text-center">
        <p className="mb-3 font-mono text-xs tracking-widest text-primary uppercase">
          The process
        </p>
        <h2 className="font-display text-3xl font-medium text-foreground sm:text-4xl">
          How it works
        </h2>
      </FadeIn>
      <FadeIn className="relative mx-auto grid max-w-3xl gap-10 sm:grid-cols-3 sm:gap-6">
        <div
          aria-hidden
          className="absolute top-5 right-0 left-0 hidden border-t border-dashed border-border sm:block"
        />
        {STEPS.map((step) => (
          <div
            key={step.n}
            className="relative flex flex-col items-center gap-3 text-center sm:items-start sm:text-left"
          >
            <span className="relative z-10 flex size-10 shrink-0 items-center justify-center rounded-full border border-border bg-background font-mono text-sm text-primary ring-4 ring-background">
              {step.n}
            </span>
            <h3 className="text-lg font-semibold text-foreground">
              {step.title}
            </h3>
            <p className="text-sm text-muted-foreground">{step.body}</p>
          </div>
        ))}
      </FadeIn>
    </Container>
  )
}

export { HowItWorks }
