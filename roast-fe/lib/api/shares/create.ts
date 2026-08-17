import { apiFetch } from "@/lib/api/client"
import type { ShareLink } from "@/lib/api/types"

/**
 * POST /api/v1/share/roasts/{roast_id}/links/ — no request body, the roast
 * comes from the URL. Idempotent: returns the roast's existing active link
 * (200) instead of creating a duplicate if one already exists (201) —
 * apiFetch doesn't distinguish the two, which is fine, the caller only
 * needs the resulting link either way.
 */
export function createOrGetShareLink(roastId: string): Promise<ShareLink> {
  return apiFetch<ShareLink>(`/api/v1/share/roasts/${roastId}/links/`, { method: "POST" })
}
