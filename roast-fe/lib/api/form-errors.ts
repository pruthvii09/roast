import type { FieldValues, Path, UseFormReturn } from "react-hook-form"

import { isApiError } from "@/lib/api/errors"

/**
 * Maps a VALIDATION_ERROR's `details` (raw DRF field-error dict) onto
 * matching react-hook-form fields. Returns whether at least one field error
 * was applied, so callers can fall back to a form-level message otherwise.
 */
export function applyApiFieldErrors<T extends FieldValues>(
  form: UseFormReturn<T>,
  details: unknown
): boolean {
  if (!details || typeof details !== "object") return false

  const values = form.getValues()
  let applied = false

  for (const [key, value] of Object.entries(details as Record<string, unknown>)) {
    if (!(key in values)) continue
    const message = Array.isArray(value) ? value.map(String).join(" ") : String(value)
    form.setError(key as Path<T>, { type: "server", message })
    applied = true
  }

  return applied
}

/** Turns any caught error (ApiError, an abort/timeout, or a raw network failure) into copy safe to show inline. */
export function getApiErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    switch (error.code) {
      case "THROTTLED":
        // Backend messages for this code are already user-facing and specific
        // (e.g. "Weekly roast limit reached (3 per 7 days)."), so prefer them.
        return (
          error.message ||
          (error.retryAfterSeconds
            ? `Too many attempts. Try again in ${error.retryAfterSeconds}s.`
            : "Too many attempts. Please wait a moment and try again.")
        )
      case "VALIDATION_ERROR":
        return "Please fix the highlighted fields and try again."
      case "EMAIL_NOT_VERIFIED":
        return "Please verify your email before logging in."
      case "PERMISSION_DENIED":
        return "You don't have permission to do that."
      case "NOT_FOUND":
        return "That couldn't be found."
      default:
        return error.message || "Something went wrong. Please try again."
    }
  }
  if (error instanceof DOMException && (error.name === "AbortError" || error.name === "TimeoutError")) {
    return "This is taking longer than expected. Please try again."
  }
  return "Network error. Check your connection and try again."
}
