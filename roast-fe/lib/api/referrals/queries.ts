import { useQuery } from "@tanstack/react-query"

import { fetchReferralInfo } from "@/lib/api/referrals/get-me"
import { queryKeys } from "@/lib/api/utils/query-keys"

export function useReferralInfoQuery() {
  return useQuery({
    queryKey: queryKeys.referrals.me,
    queryFn: fetchReferralInfo,
  })
}
