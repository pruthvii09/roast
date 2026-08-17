import { apiFetch } from "@/lib/api/client"
import type { PublicRoast } from "@/lib/api/types"

/** GET /api/v1/share/public/{token}/ — anonymous, no Authorization header sent. */
export function fetchPublicRoast(token: string): Promise<PublicRoast> {
  return apiFetch<PublicRoast>(`/api/v1/share/public/${token}/`, { auth: false })
}
