/**
 * Zustand store for client list and selected client state.
 */
import { create } from 'zustand'
import {
  fetchClients, fetchClient, fetchClientHistory,
  fetchOptimize, runAllStress, fetchAgentLog,
  fetchDashboardSummary, fetchActiveMarginCall
} from '../api/client'
import useAgentStore from './agentStore'

const useClientStore = create((set, get) => ({
  // Client list
  clients: [],
  clientsLoading: false,
  clientsError: null,

  // Selected client detail
  selectedClientId: null,
  selectedClient: null,
  clientLoading: false,

  // Dashboard stats (StatBar)
  dashboardSummary: null,

  // Filters
  filterStatus: 'all',   // 'all' | 'breach' | 'warning' | 'normal'
  searchQuery: '',

  // ── Actions ──────────────────────────────────────────────────────────────

  loadClients: async () => {
    set({ clientsLoading: true, clientsError: null })
    try {
      const clients = await fetchClients()
      set({ clients, clientsLoading: false })
    } catch (err) {
      set({ clientsError: err.message, clientsLoading: false })
    }
  },

  loadDashboardSummary: async () => {
    try {
      const summary = await fetchDashboardSummary()
      set({ dashboardSummary: summary })
    } catch {
      // Non-fatal — dashboard can render without summary
    }
  },

  selectClient: async (clientId) => {
    if (get().selectedClientId === clientId) return
    // Clear stale agent output immediately so the new client starts clean
    useAgentStore.getState().resetForClientSwitch()
    set({ selectedClientId: clientId, clientLoading: true, selectedClient: null })
    try {
      const [client, history, optimize, stress, agentLog, marginCall] = await Promise.allSettled([
        fetchClient(clientId),
        fetchClientHistory(clientId),
        fetchOptimize(clientId),
        runAllStress(clientId),
        fetchAgentLog(clientId),
        fetchActiveMarginCall(clientId)
      ])

      set({
        selectedClient: {
          ...(client.status === 'fulfilled' ? client.value : {}),
          history: history.status === 'fulfilled' ? history.value : [],
          optimize: optimize.status === 'fulfilled' ? optimize.value : null,
          stressResults: stress.status === 'fulfilled' ? stress.value : [],
          agentLog: agentLog.status === 'fulfilled' ? agentLog.value : [],
          marginCall: marginCall.status === 'fulfilled' ? marginCall.value : null
        },
        clientLoading: false
      })
    } catch (err) {
      set({ clientLoading: false })
    }
  },

  setFilter: (status) => set({ filterStatus: status }),
  setSearch: (query) => set({ searchQuery: query }),

  // Derived: filtered + searched client list
  getFilteredClients: () => {
    const { clients, filterStatus, searchQuery } = get()
    return clients
      .filter(c => filterStatus === 'all' || c.status === filterStatus)
      .filter(c =>
        !searchQuery ||
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
  },

  refreshAgentLog: async (clientId) => {
    try {
      const agentLog = await fetchAgentLog(clientId)
      const { selectedClient } = get()
      if (selectedClient && selectedClient.id === clientId) {
        set({ selectedClient: { ...selectedClient, agentLog } })
      }
    } catch {}
  },

  refreshMarginCall: async (clientId) => {
    try {
      const marginCall = await fetchActiveMarginCall(clientId)
      const { selectedClient } = get()
      if (selectedClient && selectedClient.id === clientId) {
        set({ selectedClient: { ...selectedClient, marginCall } })
      }
    } catch {}
  }
}))

export default useClientStore
