import { FadeIn } from "@/components/shared/fade-in"

function OpeningRoast({ summary, delay = 0 }: { summary: string; delay?: number }) {
  if (!summary) return null

  return (
    <FadeIn delay={delay}>
      <section aria-label="Opening roast" className="py-2 text-center sm:py-4">
        <p className="mx-auto max-w-2xl font-display text-3xl leading-[1.15] font-medium text-balance text-foreground sm:text-4xl">
          {summary}
        </p>
      </section>
    </FadeIn>
  )
}

export { OpeningRoast }
