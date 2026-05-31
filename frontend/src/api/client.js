/**
 * Axios base client. All API calls must go through this file — never fetch
 * directly in components (CLAUDE.md §15).
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// ── Clients ──────────────────────────────────────────────────────────────
export const fetchClients = () =>
  api.get('/clients').then(r => r.data)

export const fetchClient = (id) =>
  api.get(`/clients/${id}`).then(r => r.data)

export const fetchClientRisk = (id) =>
  api.get(`/clients/${id}/risk`).then(r => r.data)

export const fetchClientPortfolio = (id) =>
  api.get(`/clients/${id}/portfolio`).then(r => r.data)

export const fetchClientCollateral = (id) =>
  api.get(`/clients/${id}/collateral`).then(r => r.data)

export const fetchClientHistory = (id) =>
  api.get(`/clients/${id}/history`).then(r => r.data)

export const fetchClientCalls = (id) =>
  api.get(`/clients/${id}/calls`).then(r => r.data)

export const fetchActiveMarginCall = (id) =>
  api.get(`/clients/${id}/margin-call/active`).then(r => r.data)

export const acknowledgeMarginCall = (clientId, callId) =>
  api.post(`/clients/${clientId}/margin-call/${callId}/acknowledge`).then(r => r.data)

export const resolveMarginCall = (clientId, callId, resolutionType = 'deposit') =>
  api.post(`/clients/${clientId}/margin-call/${callId}/resolve`, null, {
    params: { resolution_type: resolutionType }
  }).then(r => r.data)

// ── Collateral optimizer ─────────────────────────────────────────────────
export const fetchOptimize = (id) =>
  api.get(`/clients/${id}/collateral/optimize`).then(r => r.data)

// ── Stress tests ─────────────────────────────────────────────────────────
export const runStress = (id, scenario, customShocks = null) =>
  api.post(`/clients/${id}/stress`, { scenario, custom_shocks: customShocks }).then(r => r.data)

export const runAllStress = (id) =>
  api.get(`/clients/${id}/stress/all`).then(r => r.data)

// ── Agent ─────────────────────────────────────────────────────────────────
export const runAgent = (id) =>
  api.post(`/agent/run/${id}`).then(r => r.data)

export const fetchAgentLog = (id) =>
  api.get(`/agent/log/${id}`).then(r => r.data)

export const generateMemo = (id, type = 'call') =>
  api.post(`/agent/memo/${id}`, { type }).then(r => r.data)

// ── Dashboard ─────────────────────────────────────────────────────────────
export const fetchDashboardSummary = () =>
  api.get('/dashboard/summary').then(r => r.data)

export const refreshMarket = () =>
  api.post('/market/refresh').then(r => r.data)

export default api
