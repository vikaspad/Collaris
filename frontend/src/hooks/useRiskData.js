/**
 * Hook: polls the client list every 30 seconds to keep risk data fresh.
 */
import { useEffect } from 'react'
import useClientStore from '../store/clientStore'

export function useRiskData() {
  const { loadClients, loadDashboardSummary } = useClientStore()

  useEffect(() => {
    loadClients()
    loadDashboardSummary()

    // Refresh every 30s
    const interval = setInterval(() => {
      loadClients()
      loadDashboardSummary()
    }, 30_000)

    return () => clearInterval(interval)
  }, [])
}
