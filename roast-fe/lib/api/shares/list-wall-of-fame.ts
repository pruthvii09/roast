import { apiFetch } from "@/lib/api/client"
import type { WallOfFameEntry } from "@/lib/api/types"

export interface ListWallOfFameParams {
  page_size?: number
  /** "top" (default, ranked by total reactions) or "new" (most recent first). */
  ordering?: "top" | "new"
}

/** GET /api/v1/share/wall-of-fame/ — anonymous, opt-in public roasts only. */
export function fetchWallOfFame(params: ListWallOfFameParams = {}): Promise<WallOfFameEntry[]> {
  const search = new URLSearchParams()
  if (params.page_size) search.set("page_size", String(params.page_size))
  if (params.ordering) search.set("ordering", params.ordering)
  const query = search.toString()
  return apiFetch<WallOfFameEntry[]>(`/api/v1/share/wall-of-fame/${query ? `?${query}` : ""}`, {
    auth: false,
  })
}
