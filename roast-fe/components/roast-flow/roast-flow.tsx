"use client"

import { useState } from "react"

import { ProcessingScreen } from "@/components/roast-flow/processing-screen"
import { StepIndicator } from "@/components/roast-flow/step-indicator"
import { StepInput } from "@/components/roast-flow/step-input"
import { StepIntensity } from "@/components/roast-flow/step-intensity"
import { StepLanguage } from "@/components/roast-flow/step-language"
import { StepReview } from "@/components/roast-flow/step-review"
import { StepType } from "@/components/roast-flow/step-type"
import type { WizardStepId } from "@/components/roast-flow/copy"
import type { Intensity, Language, RoastRun, Submission, SubmissionType } from "@/lib/api/types"

type ActiveStep = WizardStepId | "processing"

interface RoastFlowProps {
  initialType?: SubmissionType
  onClose: () => void
}

function RoastFlow({ initialType, onClose }: RoastFlowProps) {
  const [step, setStep] = useState<ActiveStep>(initialType ? "input" : "type")
  const [submissionType, setSubmissionType] = useState<SubmissionType | null>(initialType ?? null)
  const [submission, setSubmission] = useState<Submission | null>(null)
  // English/Hindi and gentle/sarcastic/brutal are shown as "coming soon"
  // (see LANGUAGE_OPTIONS/INTENSITY_OPTIONS in ./copy) rather than
  // removed, so the default here must be one of the two still-selectable
  // options — not the language/intensity that used to be default.
  const [language, setLanguage] = useState<Language>("hinglish")
  const [intensity, setIntensity] = useState<Intensity>("nuclear")
  const [roastRun, setRoastRun] = useState<RoastRun | null>(null)

  return (
    <div className="space-y-6">
      {step !== "processing" ? <StepIndicator current={step} /> : null}

      {step === "type" ? (
        <StepType
          value={submissionType}
          onChange={setSubmissionType}
          onContinue={() => {
            if (submission && submission.submission_type !== submissionType) {
              setSubmission(null)
            }
            setStep("input")
          }}
        />
      ) : null}

      {step === "input" && submissionType ? (
        <StepInput
          submissionType={submissionType}
          submission={submission}
          onSubmissionCreated={(created) => {
            setSubmission(created)
            setStep("language")
          }}
          onReplace={() => setSubmission(null)}
          onBack={() => setStep("type")}
          onContinue={() => setStep("language")}
        />
      ) : null}

      {step === "language" ? (
        <StepLanguage
          value={language}
          onChange={setLanguage}
          onBack={() => setStep("input")}
          onContinue={() => setStep("intensity")}
        />
      ) : null}

      {step === "intensity" ? (
        <StepIntensity
          value={intensity}
          onChange={setIntensity}
          onBack={() => setStep("language")}
          onContinue={() => setStep("review")}
        />
      ) : null}

      {step === "review" && submission ? (
        <StepReview
          submission={submission}
          language={language}
          intensity={intensity}
          onBack={() => setStep("intensity")}
          onRoastCreated={(run) => {
            setRoastRun(run)
            setStep("processing")
          }}
        />
      ) : null}

      {step === "processing" && roastRun && submission ? (
        <ProcessingScreen
          submission={submission}
          language={language}
          intensity={intensity}
          roastRun={roastRun}
          onDone={onClose}
        />
      ) : null}
    </div>
  )
}

export { RoastFlow }
