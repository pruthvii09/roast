import { apiFetch } from "@/lib/api/client"
import type { Submission, SubmissionCreateRequest } from "@/lib/api/types"

/**
 * POST /api/v1/submissions/ — resume submissions require multipart (a real
 * File), website/github require a source_url and must NOT include a file.
 * Extraction runs async on the backend; the returned submission starts at
 * status "processing" and transitions to "ready"/"failed" via polling.
 */
export function createSubmission(payload: SubmissionCreateRequest): Promise<Submission> {
  if (payload.submission_type === "resume") {
    const formData = new FormData()
    formData.set("submission_type", payload.submission_type)
    if (payload.title) formData.set("title", payload.title)
    if (payload.visibility) formData.set("visibility", payload.visibility)
    if (payload.file) formData.set("file", payload.file)
    return apiFetch<Submission>("/api/v1/submissions/", { method: "POST", body: formData })
  }

  return apiFetch<Submission>("/api/v1/submissions/", {
    method: "POST",
    body: {
      submission_type: payload.submission_type,
      title: payload.title,
      visibility: payload.visibility,
      source_url: payload.source_url,
    },
  })
}
