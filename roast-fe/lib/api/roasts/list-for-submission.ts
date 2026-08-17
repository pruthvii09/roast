import { apiFetch } from "@/lib/api/client"
import type { RoastRunList } from "@/lib/api/types"

/**
 * GET /api/v1/submissions/{submission_id}/roasts/ — the backend has no
 * top-level roast list; roast runs are only listable nested under their
 * submission. Newest-first, owner-scoped via the parent submission.
 */
export function fetchRoastRunsForSubmission(
  submissionId: string,
  pageSize = 10
): Promise<RoastRunList[]> {
  return apiFetch<RoastRunList[]>(
    `/api/v1/submissions/${submissionId}/roasts/?page_size=${pageSize}`
  )
}
