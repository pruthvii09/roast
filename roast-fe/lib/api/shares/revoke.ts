import { apiFetch } from "@/lib/api/client"

/** DELETE /api/v1/share/links/{id}/ — soft revoke, idempotent, 204 either way. */
export function revokeShareLink(shareLinkId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/share/links/${shareLinkId}/`, { method: "DELETE" })
}
