import { refreshAccessToken } from "@/lib/api/auth/refresh"
import { getAccessToken, setAccessToken } from "@/lib/api/auth-store"
import { ApiError } from "@/lib/api/errors"
import type { ApiErrorEnvelope } from "@/lib/api/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  /** JSON-serializable body, or a FormData instance for multipart requests. */
  body?: unknown
  /** Attach the Authorization header and retry-once-on-401. Default true. */
  auth?: boolean
  /** Internal — prevents a second refresh-and-retry after one already happened. */
  _isRetry?: boolean
}

function resolveUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) return path
  return `${API_BASE_URL}${path}`
}

function isFormData(body: unknown): body is FormData {
  return typeof FormData !== "undefined" && body instanceof FormData
}

function parseRetryAfter(res: Response): number | null {
  const header = res.headers.get("Retry-After")
  if (!header) return null
  const seconds = Number(header)
  return Number.isFinite(seconds) ? seconds : null
}

/**
 * Envelope-aware fetch wrapper for direct browser -> Django calls (every
 * endpoint except the three auth ones proxied through app/api/auth/*, which
 * use plain fetch instead since they're same-origin and cookie-based).
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, auth = true, _isRetry = false, headers, ...rest } = options

  const requestHeaders = new Headers(headers)
  let requestBody: BodyInit | undefined

  if (body !== undefined) {
    if (isFormData(body)) {
      requestBody = body
      // Let the browser set Content-Type (including the multipart boundary).
    } else {
      requestHeaders.set("Content-Type", "application/json")
      requestBody = JSON.stringify(body)
    }
  }

  if (auth) {
    const token = getAccessToken()
    if (token) requestHeaders.set("Authorization", `Bearer ${token}`)
  }

  const res = await fetch(resolveUrl(path), {
    ...rest,
    headers: requestHeaders,
    body: requestBody,
  })

  if (res.status === 401 && auth && !_isRetry) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      return apiFetch<T>(path, { ...options, _isRetry: true })
    }
    setAccessToken(null)
  }

  if (res.status === 204) {
    return undefined as T
  }

  const json = await res.json().catch(() => null)

  if (!res.ok || (json && typeof json === "object" && json.success === false)) {
    const errorEnvelope = json as ApiErrorEnvelope | null
    const requestId = errorEnvelope?.error?.request_id ?? res.headers.get("X-Request-ID")
    throw new ApiError(
      errorEnvelope?.error?.code ?? "ERROR",
      errorEnvelope?.error?.message ?? res.statusText ?? "Request failed",
      errorEnvelope?.error?.details ?? null,
      requestId,
      res.status,
      parseRetryAfter(res)
    )
  }

  return (json?.data ?? json) as T
}
