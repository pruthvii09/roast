import { apiFetch } from "@/lib/api/client"
import type { ReactionCreateRequest, ReactionTotals } from "@/lib/api/types"

/** POST /api/v1/share/public/{token}/reactions/ — anonymous, returns updated totals for all reaction types. */
export function reactToShare(token: string, payload: ReactionCreateRequest): Promise<ReactionTotals> {
  return apiFetch<ReactionTotals>(`/api/v1/share/public/${token}/reactions/`, {
    method: "POST",
    body: payload,
    auth: false,
  })
}
