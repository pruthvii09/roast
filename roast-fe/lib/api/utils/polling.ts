/**
 * Convention for future status-polling hooks (submission/roast processing,
 * neither built yet). Not wired to any query in this phase — global
 * QueryClient defaults stay conservative (no auto-refetch) and individual
 * hooks opt into polling explicitly via this helper.
 */
export function pollingRefetchInterval<S extends string>(
  status: S | undefined,
  terminalStatuses: S[],
  intervalMs = 2500
): number | false {
  if (status === undefined || terminalStatuses.includes(status)) return false
  return intervalMs
}
