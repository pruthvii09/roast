import { Languages as LanguagesIcon } from "lucide-react"

import { Container } from "@/components/shared/container"
import { FadeIn } from "@/components/shared/fade-in"

const LANGUAGES = ["English", "Hindi", "Hinglish"] as const

function Languages() {
  return (
    <Container className="py-20 sm:py-28">
      <FadeIn className="flex flex-col items-center gap-6 text-center">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">
          Languages
        </p>
        <h2 className="font-display text-3xl font-medium text-foreground sm:text-4xl">
          Roasted in your language
        </h2>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {LANGUAGES.map((lang) => (
            <span
              key={lang}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3.5 py-1.5 text-sm text-foreground"
            >
              <LanguagesIcon className="size-3.5 text-primary" />
              {lang}
            </span>
          ))}
        </div>
      </FadeIn>
    </Container>
  )
}

export { Languages }
