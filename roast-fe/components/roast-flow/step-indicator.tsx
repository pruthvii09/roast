import { Check } from "lucide-react"

import { STEP_LABELS, WIZARD_STEPS, type WizardStepId } from "@/components/roast-flow/copy"
import { cn } from "@/lib/utils"

function StepIndicator({ current }: { current: WizardStepId }) {
  const currentIndex = WIZARD_STEPS.indexOf(current)

  return (
    <ol
      aria-label={`Step ${currentIndex + 1} of ${WIZARD_STEPS.length}: ${STEP_LABELS[current]}`}
      className="flex items-center gap-1.5"
    >
      {WIZARD_STEPS.map((step, index) => {
        const isComplete = index < currentIndex
        const isCurrent = index === currentIndex
        return (
          <li key={step} className="flex flex-1 items-center gap-1.5">
            <span
              aria-hidden
              className={cn(
                "flex size-5 shrink-0 items-center justify-center rounded-full text-[0.65rem] font-medium transition-colors",
                isComplete && "bg-primary text-primary-foreground",
                isCurrent && "bg-primary/15 text-primary ring-2 ring-primary/30",
                !isComplete && !isCurrent && "bg-muted text-muted-foreground"
              )}
            >
              {isComplete ? <Check className="size-3" /> : index + 1}
            </span>
            {index < WIZARD_STEPS.length - 1 ? (
              <span
                aria-hidden
                className={cn("h-px flex-1", isComplete ? "bg-primary" : "bg-border")}
              />
            ) : null}
          </li>
        )
      })}
    </ol>
  )
}

export { StepIndicator }
