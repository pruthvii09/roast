"use client"

import { SelectableCard } from "@/components/roast-flow/selectable-card"
import { StepFooter } from "@/components/roast-flow/step-footer"
import { SUBMISSION_TYPE_OPTIONS } from "@/components/roast-flow/copy"
import type { SubmissionType } from "@/lib/api/types"

interface StepTypeProps {
  value: SubmissionType | null
  onChange: (value: SubmissionType) => void
  onContinue: () => void
}

function StepType({ value, onChange, onContinue }: StepTypeProps) {
  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <p className="font-mono text-xs tracking-widest text-primary uppercase">Step 1</p>
        <h2 className="font-display text-2xl font-medium text-foreground">
          What are you roasting?
        </h2>
      </div>
      <div role="radiogroup" aria-label="Submission type" className="grid gap-3 sm:grid-cols-3">
        {SUBMISSION_TYPE_OPTIONS.map(({ value: type, icon: Icon, label, description }) => (
          <SelectableCard
            key={type}
            name="submission-type"
            value={type}
            checked={value === type}
            onChange={(v) => onChange(v as SubmissionType)}
          >
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Icon className="size-5" strokeWidth={2} />
            </div>
            <span className="mt-4 text-base font-semibold text-foreground">{label}</span>
            <span className="mt-1 text-sm text-muted-foreground">{description}</span>
          </SelectableCard>
        ))}
      </div>
      <StepFooter onContinue={onContinue} continueDisabled={!value} />
    </div>
  )
}

export { StepType }
