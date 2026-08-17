import { apiFetch } from "@/lib/api/client"
import type { Submission } from "@/lib/api/types"

/** GET /api/v1/submissions/{id}/ — full detail, owner-scoped. */
export function fetchSubmission(submissionId: string): Promise<Submission> {
  return apiFetch<Submission>(`/api/v1/submissions/${submissionId}/`)
}
