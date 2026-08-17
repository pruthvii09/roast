/** Centralized query key factory — add to this as real data hooks are built. */
export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  submissions: {
    all: ["submissions"] as const,
    list: (params: object = {}) => ["submissions", "list", params] as const,
    status: (submissionId: string) => ["submissions", "status", submissionId] as const,
    detail: (submissionId: string) => ["submissions", "detail", submissionId] as const,
  },
  roasts: {
    forSubmission: (submissionId: string) => ["roasts", "submission", submissionId] as const,
    quota: ["roasts", "quota"] as const,
    status: (roastId: string) => ["roasts", "status", roastId] as const,
    detail: (roastId: string) => ["roasts", "detail", roastId] as const,
  },
  shares: {
    forRoast: (roastId: string) => ["shares", "roast", roastId] as const,
    public: (token: string) => ["shares", "public", token] as const,
  },
}
