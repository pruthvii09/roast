import { apiFetch } from "@/lib/api/client"
import type { PatchMeRequest, User } from "@/lib/api/types"

/** GET /api/v1/auth/me/ — direct to Django, authenticated via the in-memory access token. */
export function fetchMe(): Promise<User> {
  return apiFetch<User>("/api/v1/auth/me/")
}

/** PATCH /api/v1/auth/me/ — only display_name/avatar_url are mutable; email changes are silently ignored by the backend. */
export function updateMe(payload: PatchMeRequest): Promise<User> {
  return apiFetch<User>("/api/v1/auth/me/", { method: "PATCH", body: payload })
}
