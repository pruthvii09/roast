"use client"

import { LANGUAGE_OPTIONS } from "@/components/roast-flow/copy"
import { SelectableCard } from "@/components/roast-flow/selectable-card"
import { StepFooter } from "@/components/roast-flow/step-footer"
import type { Language } from "@/lib/api/types"

interface StepLanguageProps {
  value: Language
  onChange: (value: Language) => void
  onBack: () => void
  onContinue: () => void
}

function StepLanguage({ value, onChange, onBack, onContinue }: StepLanguageProps) {
  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Step 3</p>
        <h2 className="font-display text-2xl font-medium text-foreground">Pick a language</h2>
        <p className="text-sm text-muted-foreground">How should we deliver the news?</p>
      </div>
      <div role="radiogroup" aria-label="Roast language" className="grid gap-3 sm:grid-cols-3">
        {LANGUAGE_OPTIONS.map(({ value: lang, label, example }) => (
          <SelectableCard
            key={lang}
            name="language"
            value={lang}
            checked={value === lang}
            onChange={(v) => onChange(v as Language)}
          >
            <span className="text-base font-semibold text-foreground">{label}</span>
            <span className="mt-2 text-sm text-muted-foreground italic">{example}</span>
          </SelectableCard>
        ))}
      </div>
      <StepFooter onBack={onBack} onContinue={onContinue} />
    </div>
  )
}

export { StepLanguage }
