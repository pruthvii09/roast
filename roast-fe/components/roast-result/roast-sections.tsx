import { FadeIn } from "@/components/shared/fade-in"
import type { RoastSection } from "@/lib/api/types"

/**
 * Narrowed to the fields this component reads — a structural subset both
 * RoastSection and the public share page's PublicRoastSection satisfy.
 */
type DisplayedSection = Pick<RoastSection, "id" | "key" | "title" | "content" | "position">

function RoastSections({
  sections,
  delay = 0,
}: {
  sections: DisplayedSection[]
  delay?: number
}) {
  if (sections.length === 0) return null

  const sorted = [...sections].sort((a, b) => a.position - b.position)

  return (
    <FadeIn delay={delay}>
      <section aria-labelledby="sections-heading" className="space-y-6">
        <h2
          id="sections-heading"
          className="font-mono text-xs font-semibold tracking-widest text-muted-foreground uppercase"
        >
          The Full Breakdown
        </h2>
        <div className="space-y-7">
          {sorted.map((section) => (
            <div key={section.id}>
              <h3 className="font-display text-xl font-semibold text-foreground">{section.title}</h3>
              <p className="mt-2 leading-relaxed text-balance whitespace-pre-line text-foreground/90">
                {section.content}
              </p>
            </div>
          ))}
        </div>
      </section>
    </FadeIn>
  )
}

export { RoastSections }
