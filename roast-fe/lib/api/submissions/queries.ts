import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { createSubmission } from "@/lib/api/submissions/create"
import { fetchSubmission } from "@/lib/api/submissions/get"
import { fetchSubmissions, type ListSubmissionsParams } from "@/lib/api/submissions/list"
import { fetchSubmissionStatus } from "@/lib/api/submissions/status"
import { updateSubmission } from "@/lib/api/submissions/update"
import { uploadResumeSubmission, type UploadResumeParams } from "@/lib/api/submissions/upload-resume"
import { pollingRefetchInterval } from "@/lib/api/utils/polling"
import { queryKeys } from "@/lib/api/utils/query-keys"
import type { SubmissionCreateRequest, SubmissionStatus, SubmissionUpdateRequest } from "@/lib/api/types"

const NON_TERMINAL_SUBMISSION_STATUSES: SubmissionStatus[] = ["draft", "processing"]
const TERMINAL_SUBMISSION_STATUSES: SubmissionStatus[] = ["ready", "failed", "deleted"]

export function useSubmissionsQuery(params: ListSubmissionsParams = {}) {
  return useQuery({
    queryKey: queryKeys.submissions.list(params),
    queryFn: () => fetchSubmissions(params),
    refetchInterval: (query) => {
      const data = query.state.data
      const hasInFlight = data?.some((s) => NON_TERMINAL_SUBMISSION_STATUSES.includes(s.status))
      return hasInFlight ? 3000 : false
    },
  })
}

export function useCreateSubmissionMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SubmissionCreateRequest) => createSubmission(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.submissions.all }),
  })
}

/** Resume-specific — uses XHR under the hood so callers can track upload progress. */
export function useUploadResumeMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: UploadResumeParams) => uploadResumeSubmission(params),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.submissions.all }),
  })
}

/** Polls the lightweight status endpoint — pass `enabled: false` until a submission id exists. */
export function useSubmissionStatusQuery(submissionId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.submissions.status(submissionId),
    queryFn: () => fetchSubmissionStatus(submissionId),
    enabled,
    refetchInterval: (query) =>
      pollingRefetchInterval(query.state.data?.status, TERMINAL_SUBMISSION_STATUSES),
  })
}

/** Full detail (title/type/source_url/assets) — used by the roast result page's header. */
export function useSubmissionQuery(submissionId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.submissions.detail(submissionId),
    queryFn: () => fetchSubmission(submissionId),
    enabled,
  })
}

/** Used by the share dialog's "Feature on Wall of Fame" toggle (sets `visibility`). */
export function useUpdateSubmissionMutation(submissionId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SubmissionUpdateRequest) => updateSubmission(submissionId, payload),
    onSuccess: (submission) => {
      queryClient.setQueryData(queryKeys.submissions.detail(submissionId), submission)
      queryClient.invalidateQueries({ queryKey: queryKeys.submissions.all })
    },
  })
}
