import { apiFetch } from "@/lib/api/client"
import type { RoastRunStatusPoll } from "@/lib/api/types"

/** GET /api/v1/roasts/{id}/status/ — lightweight poll target, no nested sections/findings. */
export function fetchRoastRunStatus(roastId: string): Promise<RoastRunStatusPoll> {
  return apiFetch<RoastRunStatusPoll>(`/api/v1/roasts/${roastId}/status/`)
}
