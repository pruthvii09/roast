import { apiFetch } from "@/lib/api/client"
import type { SubmissionStatusPoll } from "@/lib/api/types"

/** GET /api/v1/submissions/{id}/status/ — lightweight poll target, no extracted_text/metadata. */
export function fetchSubmissionStatus(submissionId: string): Promise<SubmissionStatusPoll> {
  return apiFetch<SubmissionStatusPoll>(`/api/v1/submissions/${submissionId}/status/`)
}
