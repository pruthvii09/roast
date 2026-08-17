import { isApiError } from "@/lib/api/errors"
import { getApiErrorMessage } from "@/lib/api/form-errors"

export { applyApiFieldErrors } from "@/lib/api/form-errors"

/** Same as getApiErrorMessage, but special-cases 401s with copy that doesn't leak whether an email exists. */
export function getAuthErrorMessage(error: unknown): string {
  if (isApiError(error) && error.code === "AUTHENTICATION_FAILED") {
    return "Invalid email or password."
  }
  return getApiErrorMessage(error)
}
