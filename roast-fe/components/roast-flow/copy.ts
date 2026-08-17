import { Feather, FileText, Flame, GitBranch, Globe, MessageSquareQuote, Skull } from "lucide-react"

import type { Intensity, Language, SubmissionType } from "@/lib/api/types"

export const SUBMISSION_TYPE_OPTIONS: {
  value: SubmissionType
  icon: typeof FileText
  label: string
  description: string
  detail: string
}[] = [
  {
    value: "resume",
    icon: FileText,
    label: "Resume",
    description: "Upload a PDF or Word doc.",
    detail: "PDF, DOC, or DOCX — up to 10MB.",
  },
  {
    value: "website",
    icon: Globe,
    label: "Website",
    description: "Portfolio, landing page, or personal site.",
    detail: "Any public URL.",
  },
  {
    value: "github",
    icon: GitBranch,
    label: "GitHub",
    description: "A profile or a specific repository.",
    detail: "Any github.com URL.",
  },
]

export const LANGUAGE_OPTIONS: {
  value: Language
  label: string
  example: string
}[] = [
  {
    value: "en",
    label: "English",
    example: "“This resume is full of buzzwords, not results.”",
  },
  {
    value: "hi",
    label: "Hindi",
    example: "“यह रिज़्यूमे शब्दों से भरा है, नतीजों से नहीं।”",
  },
  {
    value: "hinglish",
    label: "Hinglish",
    example: "“Resume mein buzzwords zyada hain, results kam.”",
  },
]

export const INTENSITY_OPTIONS: {
  value: Intensity
  label: string
  tagline: string
  icon: typeof FileText
  level: number
  tone: string
  chipClass: string
}[] = [
  {
    value: "gentle",
    label: "Gentle",
    tagline: "Some teasing",
    icon: Feather,
    level: 1,
    tone: "text-muted-foreground",
    chipClass: "border-border bg-muted/60 text-muted-foreground",
  },
  {
    value: "sarcastic",
    label: "Sarcastic",
    tagline: "You're asking for it",
    icon: MessageSquareQuote,
    level: 2,
    tone: "text-foreground",
    chipClass: "border-primary/30 bg-primary/10 text-primary",
  },
  {
    value: "brutal",
    label: "Brutal",
    tagline: "No mercy",
    icon: Flame,
    level: 3,
    tone: "text-warning",
    chipClass: "border-warning/30 bg-warning/10 text-warning",
  },
  {
    value: "nuclear",
    label: "Nuclear",
    tagline: "God has left the chat",
    icon: Skull,
    level: 4,
    tone: "text-destructive",
    chipClass: "border-destructive/30 bg-destructive/10 text-destructive",
  },
]

/** Nuclear-only callout shown wherever the intensity is displayed prominently (review step, processing screen). */
export const NUCLEAR_WARNING = "Proceed at your own risk."

/**
 * Purely decorative UI copy for the processing screen — rotates while a
 * roast run is queued/processing. Deliberately generic/playful rather than
 * naming real pipeline stages, since the backend only ever reports
 * queued/processing/completed/failed and nothing more granular.
 */
export const PROCESSING_OPENING_MESSAGE: Record<SubmissionType, string> = {
  resume: "Reading your resume…",
  website: "Scanning your website…",
  github: "Digging through your commits…",
}

export const PROCESSING_MESSAGES = [
  "Finding the questionable decisions…",
  "Consulting the AI…",
  "Preparing the damage…",
  "Almost done…",
]

/** Cycled once the scripted sequence above runs out but the run still isn't terminal — never loops back to the opening line, which would wrongly imply work had restarted. */
export const PROCESSING_FINAL_STRETCH_MESSAGES = [
  "Almost done…",
  "Good roasts can't be rushed…",
  "Just polishing the burns…",
]

export const WIZARD_STEPS = ["type", "input", "language", "intensity", "review"] as const
export type WizardStepId = (typeof WIZARD_STEPS)[number]

export const STEP_LABELS: Record<WizardStepId, string> = {
  type: "What",
  input: "Give it",
  language: "Language",
  intensity: "Intensity",
  review: "Review",
}

export const ACCEPTED_RESUME_EXTENSIONS = [".pdf", ".doc", ".docx"]
export const ACCEPTED_RESUME_MIME_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]
export const MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024
