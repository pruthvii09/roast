import { apiFetch } from "@/lib/api/client"
import type { RoastQuota } from "@/lib/api/types"

/** GET /api/v1/roasts/quota/ — computed live, not paginated/model-backed. */
export function fetchRoastQuota(): Promise<RoastQuota> {
  return apiFetch<RoastQuota>("/api/v1/roasts/quota/")
}
