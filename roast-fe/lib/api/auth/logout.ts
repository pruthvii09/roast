import { getAccessToken, setAccessToken } from "@/lib/api/auth-store"

/**
 * Best-effort: clears local state unconditionally even if the network call
 * fails or the access token was already expired — a broken logout call must
 * never leave the user stuck in an "authenticated" client state.
 */
export async function logout(): Promise<void> {
  const token = getAccessToken()
  try {
    await fetch("/api/auth/logout", {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    })
  } finally {
    setAccessToken(null)
  }
}
