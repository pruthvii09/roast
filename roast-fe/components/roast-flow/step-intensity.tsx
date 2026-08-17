"use client"

import { TriangleAlert } from "lucide-react"

import { INTENSITY_OPTIONS, NUCLEAR_WARNING } from "@/components/roast-flow/copy"
import { SelectableCard } from "@/components/roast-flow/selectable-card"
import { StepFooter } from "@/components/roast-flow/step-footer"
import type { Intensity } from "@/lib/api/types"
import { cn } from "@/lib/utils"

interface StepIntensityProps {
  value: Intensity
  onChange: (value: Intensity) => void
  onBack: () => void
  onContinue: () => void
}

// Escalating accent per intensity so the *selected* state — not just the
// icon color — reads as "this gets more dangerous," matching the tone/
// chipClass progression INTENSITY_OPTIONS already defines (gray -> primary
// -> warning -> destructive) elsewhere in the app (e.g. roast-result-header).
const ACTIVE_CARD_CLASSNAME: Record<Intensity, string> = {
  gentle: "border-border bg-muted/40 ring-1 ring-border",
  sarcastic: "border-primary/40 bg-primary/[0.03] ring-1 ring-primary/20",
  brutal: "border-warning/40 bg-warning/[0.04] ring-1 ring-warning/25",
  nuclear: "border-destructive/40 bg-destructive/[0.04] ring-1 ring-destructive/25",
}

const ACTIVE_INDICATOR_CLASSNAME: Record<Intensity, string> = {
  gentle: "border-muted-foreground/50 bg-muted-foreground text-background",
  sarcastic: "border-primary bg-primary text-primary-foreground",
  brutal: "border-warning bg-warning text-white",
  nuclear: "border-destructive bg-destructive text-white",
}

// Same escalating axis as the two maps above — deliberately independent of
// INTENSITY_OPTIONS' `tone` field, which picks icon colors for legibility
// (sarcastic's icon is text-foreground, not text-primary) rather than this
// solid-fill accent progression.
const LEVEL_BAR_CLASSNAME: Record<Intensity, string> = {
  gentle: "bg-muted-foreground",
  sarcastic: "bg-primary",
  brutal: "bg-warning",
  nuclear: "bg-destructive",
}

function StepIntensity({ value, onChange, onBack, onContinue }: StepIntensityProps) {
  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Step 4</p>
        <h2 className="font-display text-2xl font-medium text-foreground">Choose how brutal</h2>
      </div>
      <div
        role="radiogroup"
        aria-label="Roast intensity"
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
      >
        {INTENSITY_OPTIONS.map(({ value: intensity, label, tagline, icon: Icon, level, tone, chipClass }) => (
          <SelectableCard
            key={intensity}
            name="intensity"
            value={intensity}
            checked={value === intensity}
            onChange={(v) => onChange(v as Intensity)}
            activeClassName={ACTIVE_CARD_CLASSNAME[intensity]}
            activeIndicatorClassName={ACTIVE_INDICATOR_CLASSNAME[intensity]}
          >
            <span
              className={cn(
                "flex size-9 items-center justify-center rounded-full border",
                chipClass
              )}
            >
              <Icon className={cn("size-4.5", tone)} strokeWidth={2} />
            </span>
            <span className="mt-3 text-base font-semibold text-foreground">{label}</span>
            <span className="mt-1 text-sm text-muted-foreground">{tagline}</span>
            <div className="mt-4 flex gap-1">
              {[1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  aria-hidden
                  className={cn(
                    "h-1.5 flex-1 rounded-full transition-colors",
                    i <= level ? LEVEL_BAR_CLASSNAME[intensity] : "bg-muted"
                  )}
                />
              ))}
            </div>
            {intensity === "nuclear" ? (
              <div className="mt-3 flex items-start gap-1.5 text-xs font-medium text-destructive">
                <TriangleAlert className="size-3.5 shrink-0 translate-y-px" aria-hidden />
                <span>{NUCLEAR_WARNING}</span>
              </div>
            ) : null}
          </SelectableCard>
        ))}
      </div>
      <StepFooter onBack={onBack} onContinue={onContinue} />
    </div>
  )
}

export { StepIntensity }
