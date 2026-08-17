"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { ExternalLink, RotateCcw } from "lucide-react"
import { useForm, useWatch } from "react-hook-form"
import { z } from "zod"

import { ResumeDropzone } from "@/components/roast-flow/resume-dropzone"
import { StepFooter } from "@/components/roast-flow/step-footer"
import {
  ACCEPTED_RESUME_EXTENSIONS,
  MAX_RESUME_SIZE_BYTES,
  SUBMISSION_TYPE_OPTIONS,
} from "@/components/roast-flow/copy"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { isApiError } from "@/lib/api/errors"
import { applyApiFieldErrors, getApiErrorMessage } from "@/lib/api/form-errors"
import { useCreateSubmissionMutation, useUploadResumeMutation } from "@/lib/api/submissions/queries"
import type { Submission, SubmissionType } from "@/lib/api/types"

const resumeSchema = z.object({
  title: z.string().max(255, "Keep it under 255 characters.").optional(),
  file: z
    .instanceof(File, { message: "Choose a file to upload." })
    .refine((f) => f.size > 0, "That file looks empty.")
    .refine((f) => f.size <= MAX_RESUME_SIZE_BYTES, "File must be under 10MB.")
    .refine((f) => {
      const ext = `.${f.name.split(".").pop()?.toLowerCase() ?? ""}`
      return ACCEPTED_RESUME_EXTENSIONS.includes(ext)
    }, "We only accept PDF, DOC, or DOCX files."),
})
type ResumeFormValues = z.infer<typeof resumeSchema>

function buildUrlSchema(kind: "website" | "github") {
  return z.object({
    title: z.string().max(255, "Keep it under 255 characters.").optional(),
    source_url: z
      .string()
      .min(1, "Enter a URL.")
      .url("Enter a valid URL.")
      .refine((url) => {
        if (kind !== "github") return true
        try {
          const host = new URL(url).hostname.toLowerCase()
          return host === "github.com" || host === "www.github.com"
        } catch {
          return false
        }
      }, "Must be a github.com URL."),
  })
}
type UrlFormValues = z.infer<ReturnType<typeof buildUrlSchema>>

interface StepInputProps {
  submissionType: SubmissionType
  submission: Submission | null
  onSubmissionCreated: (submission: Submission) => void
  onReplace: () => void
  onBack: () => void
  onContinue: () => void
}

function AlreadySubmitted({
  submission,
  onReplace,
  onBack,
  onContinue,
}: {
  submission: Submission
  onReplace: () => void
  onBack: () => void
  onContinue: () => void
}) {
  const option = SUBMISSION_TYPE_OPTIONS.find((o) => o.value === submission.submission_type)
  const Icon = option?.icon

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-border bg-card p-4">
        <div className="flex items-center gap-3">
          {Icon ? (
            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Icon className="size-5" />
            </div>
          ) : null}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-foreground">
              {submission.title ||
                submission.source_url ||
                submission.assets[0]?.original_filename ||
                "Your submission"}
            </p>
            <p className="text-xs text-muted-foreground">Submitted — we&apos;re on it.</p>
          </div>
          <button
            type="button"
            onClick={onReplace}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
          >
            <RotateCcw className="size-3" />
            Replace
          </button>
        </div>
      </div>
      <StepFooter onBack={onBack} onContinue={onContinue} />
    </div>
  )
}

function StepInput({
  submissionType,
  submission,
  onSubmissionCreated,
  onReplace,
  onBack,
  onContinue,
}: StepInputProps) {
  const [formError, setFormError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const uploadResume = useUploadResumeMutation()
  const createSubmission = useCreateSubmissionMutation()

  const resumeForm = useForm<ResumeFormValues>({
    resolver: zodResolver(resumeSchema),
    defaultValues: { title: "" },
  })
  const urlForm = useForm<UrlFormValues>({
    resolver: zodResolver(buildUrlSchema(submissionType === "github" ? "github" : "website")),
    defaultValues: { title: "", source_url: "" },
  })
  const watchedUrl = useWatch({ control: urlForm.control, name: "source_url" })
  const watchedFile = useWatch({ control: resumeForm.control, name: "file" })

  const isSubmitting = uploadResume.isPending || createSubmission.isPending

  if (submission) {
    return (
      <div className="space-y-5">
        <StepHeader submissionType={submissionType} />
        <AlreadySubmitted
          submission={submission}
          onReplace={onReplace}
          onBack={onBack}
          onContinue={onContinue}
        />
      </div>
    )
  }

  async function onSubmitResume(values: ResumeFormValues) {
    setFormError(null)
    setUploadProgress(0)
    try {
      const created = await uploadResume.mutateAsync({
        file: values.file,
        title: values.title || undefined,
        onProgress: setUploadProgress,
      })
      onSubmissionCreated(created)
    } catch (error) {
      setUploadProgress(null)
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(resumeForm, error.details)
        if (!applied) setFormError(getApiErrorMessage(error))
      } else {
        setFormError(getApiErrorMessage(error))
      }
    }
  }

  async function onSubmitUrl(values: UrlFormValues) {
    setFormError(null)
    try {
      const created = await createSubmission.mutateAsync({
        submission_type: submissionType,
        title: values.title || undefined,
        source_url: values.source_url,
      })
      onSubmissionCreated(created)
    } catch (error) {
      if (isApiError(error) && error.code === "VALIDATION_ERROR") {
        const applied = applyApiFieldErrors(urlForm, error.details)
        if (!applied) setFormError(getApiErrorMessage(error))
      } else {
        setFormError(getApiErrorMessage(error))
      }
    }
  }

  let parsedHost: string | null = null
  if (watchedUrl) {
    try {
      parsedHost = new URL(watchedUrl).hostname
    } catch {
      parsedHost = null
    }
  }

  return (
    <div className="space-y-5">
      <StepHeader submissionType={submissionType} />

      {formError ? (
        <Alert variant="destructive">
          <AlertDescription>{formError}</AlertDescription>
        </Alert>
      ) : null}

      {submissionType === "resume" ? (
        <Form {...resumeForm}>
          <form onSubmit={resumeForm.handleSubmit(onSubmitResume)} className="space-y-4">
            <FormField
              control={resumeForm.control}
              name="file"
              render={({ field: { onChange } }) => (
                <FormItem>
                  <FormLabel>Resume file</FormLabel>
                  <FormControl>
                    <ResumeDropzone
                      id="resume-file"
                      file={watchedFile ?? null}
                      onFileChange={(f) => onChange(f)}
                      uploadProgress={uploadProgress}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={resumeForm.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title (optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. Senior Engineer resume" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <StepFooter
              onBack={onBack}
              continueType="submit"
              continueLabel="Upload & continue"
              continueLoading={isSubmitting}
            />
          </form>
        </Form>
      ) : (
        <Form {...urlForm}>
          <form onSubmit={urlForm.handleSubmit(onSubmitUrl)} className="space-y-4">
            <FormField
              control={urlForm.control}
              name="source_url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    {submissionType === "github" ? "GitHub URL" : "Website URL"}
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="url"
                      autoComplete="url"
                      placeholder={
                        submissionType === "github"
                          ? "https://github.com/yourname"
                          : "https://yoursite.com"
                      }
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {parsedHost ? (
              <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                <ExternalLink className="size-3.5 shrink-0" />
                <span className="truncate">
                  This is what we&apos;ll roast: <span className="text-foreground">{parsedHost}</span>
                </span>
              </div>
            ) : null}
            <FormField
              control={urlForm.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title (optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. My portfolio" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <StepFooter onBack={onBack} continueType="submit" continueLoading={isSubmitting} />
          </form>
        </Form>
      )}
    </div>
  )
}

function StepHeader({ submissionType }: { submissionType: SubmissionType }) {
  const option = SUBMISSION_TYPE_OPTIONS.find((o) => o.value === submissionType)
  return (
    <div className="space-y-1 text-center">
      <p className="font-mono text-xs tracking-widest text-primary uppercase">Step 2</p>
      <h2 className="font-display text-2xl font-medium text-foreground">Give it to us</h2>
      <p className="text-sm text-muted-foreground">{option?.detail}</p>
    </div>
  )
}

export { StepInput }
