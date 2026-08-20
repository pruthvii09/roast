import { apiFetch } from "@/lib/api/client"
import type { Submission, SubmissionUpdateRequest } from "@/lib/api/types"

/** PATCH /api/v1/submissions/{id}/ — title/visibility are the only mutable fields. */
export function updateSubmission(
  submissionId: string,
  payload: SubmissionUpdateRequest
): Promise<Submission> {
  return apiFetch<Submission>(`/api/v1/submissions/${submissionId}/`, {
    method: "PATCH",
    body: payload,
  })
}
