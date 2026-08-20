import { apiFetch } from "@/lib/api/client"
import type { ReferralInfo } from "@/lib/api/types"

/** GET /api/v1/referrals/me/ — get-or-creates the caller's referral code. */
export function fetchReferralInfo(): Promise<ReferralInfo> {
  return apiFetch<ReferralInfo>("/api/v1/referrals/me/")
}
