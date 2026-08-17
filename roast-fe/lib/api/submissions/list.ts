import { apiFetch } from "@/lib/api/client"
import type { SubmissionList, SubmissionStatus, SubmissionType } from "@/lib/api/types"

export interface ListSubmissionsParams {
  page_size?: number
  submission_type?: SubmissionType
  status?: SubmissionStatus
}

/** GET /api/v1/submissions/ — owner-scoped, newest-first, no client-controllable ordering. */
export function fetchSubmissions(params: ListSubmissionsParams = {}): Promise<SubmissionList[]> {
  const search = new URLSearchParams()
  if (params.page_size) search.set("page_size", String(params.page_size))
  if (params.submission_type) search.set("submission_type", params.submission_type)
  if (params.status) search.set("status", params.status)
  const query = search.toString()
  return apiFetch<SubmissionList[]>(`/api/v1/submissions/${query ? `?${query}` : ""}`)
}
