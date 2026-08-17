import { apiFetch } from "@/lib/api/client"
import type { ShareLinkList } from "@/lib/api/types"

/** GET /api/v1/share/roasts/{roast_id}/links/ — active + revoked history, newest first, owner-scoped. */
export function fetchShareLinksForRoast(roastId: string): Promise<ShareLinkList[]> {
  return apiFetch<ShareLinkList[]>(`/api/v1/share/roasts/${roastId}/links/`)
}
