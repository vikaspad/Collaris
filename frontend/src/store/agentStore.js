/**
 * Zustand store for agent streaming and memo state.
 */
import { create } from 'zustand'
import { runAgent, generateMemo } from '../api/client'

const useAgentStore = create((set, get) => ({
  // Streaming state
  isStreaming: false,
  streamLogs: [],      // List of { node, log, action_tier, mrs_score }
  streamError: null,
  streamEventSource: null,

  // Memo generation
  memoText: '',
  memoLoading: false,
  memoError: null,

  // Agent run status
  runLoading: false,
  runResult: null,

  // ── Actions ────────────────────────────────────────────────────────────

  startStream: (clientId) => {
    // Close any existing stream
    const existing = get().streamEventSource
    if (existing) existing.close()

    set({ isStreaming: true, streamLogs: [], streamError: null })

    const es = new EventSource(`/api/agent/stream/${clientId}`)

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.done) {
          es.close()
          set({ isStreaming: false, streamEventSource: null })
        } else if (data.error) {
          set({ isStreaming: false, streamError: data.error, streamEventSource: null })
          es.close()
        } else {
          set(state => ({ streamLogs: [...state.streamLogs, data] }))
        }
      } catch {}
    }

    es.onerror = () => {
      set({ isStreaming: false, streamError: 'Stream connection lost', streamEventSource: null })
      es.close()
    }

    set({ streamEventSource: es })
  },

  stopStream: () => {
    const es = get().streamEventSource
    if (es) es.close()
    set({ isStreaming: false, streamEventSource: null })
  },

  triggerRun: async (clientId) => {
    set({ runLoading: true, runResult: null })
    try {
      const result = await runAgent(clientId)
      set({ runLoading: false, runResult: result })
      return result
    } catch (err) {
      set({ runLoading: false })
      throw err
    }
  },

  generateMemo: async (clientId, type = 'call') => {
    set({ memoLoading: true, memoError: null, memoText: '' })
    try {
      const result = await generateMemo(clientId, type)
      set({ memoLoading: false, memoText: result.memo_text })
    } catch (err) {
      set({ memoLoading: false, memoError: err.message })
    }
  },

  clearMemo: () => set({ memoText: '', memoError: null }),
  clearLogs: () => set({ streamLogs: [] }),

  // Called whenever the selected client changes — wipes all per-client state
  resetForClientSwitch: () => {
    const { streamEventSource } = get()
    if (streamEventSource) streamEventSource.close()
    set({
      isStreaming: false, streamLogs: [], streamError: null, streamEventSource: null,
      memoText: '', memoLoading: false, memoError: null,
      runLoading: false, runResult: null,
    })
  }
}))

export default useAgentStore
