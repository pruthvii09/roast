import { apiFetch } from "@/lib/api/client"
import type { RoastRun } from "@/lib/api/types"

/** GET /api/v1/roasts/{id}/ — full detail incl. score/summary/final_verdict/sections/findings. */
export function fetchRoastRun(roastId: string): Promise<RoastRun> {
  return apiFetch<RoastRun>(`/api/v1/roasts/${roastId}/`)
}
