/**
 * In-memory-only store for the JWT access token. Deliberately a plain module
 * (not React state) so lib/api/client.ts can read/write it synchronously
 * without importing React or creating a context import cycle. Never persisted
 * (no localStorage/sessionStorage) — the refresh token that would let this be
 * rehydrated lives in an httpOnly cookie instead, see app/api/auth/refresh.
 */

let accessToken: string | null = null
const listeners = new Set<() => void>()

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
  listeners.forEach((listener) => listener())
}

export function subscribeAccessToken(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
