import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"

interface StepFooterProps {
  onBack?: () => void
  onContinue?: () => void
  continueLabel?: string
  continueDisabled?: boolean
  continueLoading?: boolean
  continueType?: "button" | "submit"
}

function StepFooter({
  onBack,
  onContinue,
  continueLabel = "Continue",
  continueDisabled = false,
  continueLoading = false,
  continueType = "button",
}: StepFooterProps) {
  return (
    <div className="flex items-center justify-between gap-3 pt-2">
      {onBack ? (
        <Button type="button" variant="ghost" size="sm" className="rounded-full" onClick={onBack}>
          <ArrowLeft />
          Back
        </Button>
      ) : (
        <span />
      )}
      <Button
        type={continueType}
        size="sm"
        className="rounded-full px-5"
        disabled={continueDisabled || continueLoading}
        onClick={continueType === "button" ? onContinue : undefined}
      >
        {continueLoading ? <Loader2 className="animate-spin" /> : null}
        {continueLabel}
        {!continueLoading ? <ArrowRight /> : null}
      </Button>
    </div>
  )
}

export { StepFooter }
