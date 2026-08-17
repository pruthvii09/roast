import { apiFetch } from "@/lib/api/client"
import type { ChangePasswordRequest } from "@/lib/api/types"

/** POST /api/v1/auth/change-password/ — blacklists all other outstanding refresh tokens on success. */
export function changePassword(payload: ChangePasswordRequest): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>("/api/v1/auth/change-password/", {
    method: "POST",
    body: payload,
  })
}
