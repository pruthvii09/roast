import type { ApiErrorCode } from "@/lib/api/types"

export class ApiError extends Error {
  code: ApiErrorCode
  details: unknown
  requestId: string | null
  status: number
  retryAfterSeconds: number | null

  constructor(
    code: ApiErrorCode,
    message: string,
    details: unknown,
    requestId: string | null,
    status: number,
    retryAfterSeconds: number | null = null
  ) {
    super(message)
    this.name = "ApiError"
    this.code = code
    this.details = details
    this.requestId = requestId
    this.status = status
    this.retryAfterSeconds = retryAfterSeconds
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}
