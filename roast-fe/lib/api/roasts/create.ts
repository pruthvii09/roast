import { apiFetch } from "@/lib/api/client"
import type { RoastRun, RoastRunCreateRequest } from "@/lib/api/types"

/**
 * POST /api/v1/submissions/{submission_id}/roasts/ — submission id lives in
 * the URL, not the body. The backend requires the submission to already be
 * "ready" and enforces a weekly quota (429 THROTTLED if exceeded). A
 * duplicate in-flight request for the same (submission, language, intensity)
 * returns the existing run with 200 instead of creating a new one — apiFetch
 * doesn't distinguish 200 from 201 here, which is fine, the caller only
 * needs the resulting run either way.
 */
export function createRoastRun(
  submissionId: string,
  payload: RoastRunCreateRequest
): Promise<RoastRun> {
  return apiFetch<RoastRun>(`/api/v1/submissions/${submissionId}/roasts/`, {
    method: "POST",
    body: payload,
  })
}
