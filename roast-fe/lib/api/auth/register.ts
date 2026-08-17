import { apiFetch } from "@/lib/api/client"
import type { RegisterRequest, User } from "@/lib/api/types"

/**
 * POST /api/v1/auth/register/ — direct to Django (auth: false, no access
 * token exists yet). Registration does not return tokens, only the created
 * user; the caller must follow up with login() to establish a session.
 */
export function register(payload: RegisterRequest): Promise<User> {
  return apiFetch<User>("/api/v1/auth/register/", {
    method: "POST",
    body: payload,
    auth: false,
  })
}
