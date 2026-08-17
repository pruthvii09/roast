import { refreshAccessToken } from "@/lib/api/auth/refresh"
import { getAccessToken, setAccessToken } from "@/lib/api/auth-store"
import { ApiError } from "@/lib/api/errors"
import type { ApiErrorEnvelope, Submission, Visibility } from "@/lib/api/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

export interface UploadResumeParams {
  file: File
  title?: string
  visibility?: Visibility
  onProgress?: (percent: number) => void
  signal?: AbortSignal
}

interface XhrResult {
  status: number
  json: unknown
}

function buildFormData(params: UploadResumeParams): FormData {
  const formData = new FormData()
  formData.set("submission_type", "resume")
  if (params.title) formData.set("title", params.title)
  if (params.visibility) formData.set("visibility", params.visibility)
  formData.set("file", params.file)
  return formData
}

function xhrUploadOnce(
  formData: FormData,
  token: string | null,
  onProgress: ((percent: number) => void) | undefined,
  signal: AbortSignal | undefined
): Promise<XhrResult> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open("POST", `${API_BASE_URL}/api/v1/submissions/`)
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`)

    xhr.upload.onprogress = (event) => {
      if (onProgress && event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }
    xhr.onload = () => {
      let json: unknown = null
      try {
        json = JSON.parse(xhr.responseText)
      } catch {
        // non-JSON response (e.g. a proxy error page) — json stays null, handled by the caller
      }
      resolve({ status: xhr.status, json })
    }
    xhr.onerror = () => reject(new TypeError("Network error"))
    xhr.ontimeout = () => reject(new DOMException("Upload timed out", "TimeoutError"))
    xhr.timeout = 60_000

    if (signal) {
      if (signal.aborted) {
        xhr.abort()
        reject(new DOMException("Aborted", "AbortError"))
        return
      }
      signal.addEventListener("abort", () => {
        xhr.abort()
        reject(new DOMException("Aborted", "AbortError"))
      })
    }

    xhr.send(formData)
  })
}

/**
 * POST /api/v1/submissions/ for resume uploads specifically — uses XHR
 * instead of the shared apiFetch/fetch wrapper because fetch has no
 * upload-progress event; everything else (auth header, 401-retry-once,
 * envelope/error parsing) mirrors apiFetch's behavior by hand.
 */
export async function uploadResumeSubmission(params: UploadResumeParams): Promise<Submission> {
  const formData = buildFormData(params)
  const token = getAccessToken()
  let { status, json } = await xhrUploadOnce(formData, token, params.onProgress, params.signal)

  if (status === 401) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      ;({ status, json } = await xhrUploadOnce(formData, newToken, params.onProgress, params.signal))
    } else {
      setAccessToken(null)
    }
  }

  const body = json as (ApiErrorEnvelope & { data?: never }) | { success: true; data: Submission } | null

  if (status < 200 || status >= 300 || !body || body.success === false) {
    const errorEnvelope = body as ApiErrorEnvelope | null
    throw new ApiError(
      errorEnvelope?.error?.code ?? "ERROR",
      errorEnvelope?.error?.message ?? "Upload failed. Please try again.",
      errorEnvelope?.error?.details ?? null,
      errorEnvelope?.error?.request_id ?? null,
      status || 0,
      null
    )
  }

  return body.data
}
