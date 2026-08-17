import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { createRoastRun } from "@/lib/api/roasts/create"
import { fetchRoastRun } from "@/lib/api/roasts/get"
import { fetchRoastRunsForSubmission } from "@/lib/api/roasts/list-for-submission"
import { fetchRoastQuota } from "@/lib/api/roasts/quota"
import { fetchRoastRunStatus } from "@/lib/api/roasts/status"
import { pollingRefetchInterval } from "@/lib/api/utils/polling"
import { queryKeys } from "@/lib/api/utils/query-keys"
import type { ExtractionStatus, RoastRunCreateRequest } from "@/lib/api/types"

const NON_TERMINAL_ROAST_STATUSES: ExtractionStatus[] = ["queued", "processing"]
const TERMINAL_ROAST_STATUSES: ExtractionStatus[] = ["completed", "failed"]

/** Only fetched on demand (enabled) — the backend has no top-level roast list, so this is called per-submission when its row is expanded. */
export function useRoastRunsForSubmissionQuery(submissionId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.roasts.forSubmission(submissionId),
    queryFn: () => fetchRoastRunsForSubmission(submissionId),
    enabled,
    refetchInterval: (query) => {
      const data = query.state.data
      const hasInFlight = data?.some((r) => NON_TERMINAL_ROAST_STATUSES.includes(r.status))
      return hasInFlight ? 3000 : false
    },
  })
}

export function useCreateRoastRunMutation(submissionId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: RoastRunCreateRequest) => createRoastRun(submissionId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.roasts.forSubmission(submissionId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.roasts.quota })
    },
  })
}

export function useRoastQuotaQuery() {
  return useQuery({
    queryKey: queryKeys.roasts.quota,
    queryFn: fetchRoastQuota,
    staleTime: 30_000,
  })
}

/**
 * Polls the lightweight status endpoint for one specific run — used by the
 * New Roast flow's processing screen. `refetchIntervalInBackground: false`
 * (the TanStack default, set explicitly here for clarity) means the timer
 * keeps ticking but skips the actual network request while the tab is
 * hidden; the processing screen nudges an immediate refetch on visibility
 * regain instead of waiting for the next tick.
 */
export function useRoastRunStatusQuery(roastId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.roasts.status(roastId),
    queryFn: () => fetchRoastRunStatus(roastId),
    enabled,
    refetchInterval: (query) =>
      pollingRefetchInterval(query.state.data?.status, TERMINAL_ROAST_STATUSES),
    refetchIntervalInBackground: false,
  })
}

/** Full detail (score/summary/final_verdict/findings) — fetched once a run reaches a terminal status. */
export function useRoastRunQuery(roastId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.roasts.detail(roastId),
    queryFn: () => fetchRoastRun(roastId),
    enabled,
  })
}
