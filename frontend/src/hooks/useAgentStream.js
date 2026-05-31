/**
 * Hook: convenience wrapper around the agent streaming store.
 */
import useAgentStore from '../store/agentStore'

export function useAgentStream(clientId) {
  const { isStreaming, streamLogs, streamError, startStream, stopStream } = useAgentStore()

  const start = () => {
    if (clientId) startStream(clientId)
  }

  return { isStreaming, streamLogs, streamError, start, stop: stopStream }
}
