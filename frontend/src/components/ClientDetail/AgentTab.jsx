/**
 * Agent Actions tab — memo generator, SSE stream log, activity log.
 */
import { useState } from 'react'
import AgentMemoBox from '../shared/AgentMemoBox'
import useAgentStore from '../../store/agentStore'
import useClientStore from '../../store/clientStore'

const TIER_COLORS = { breach: '#ff4444', warning: '#f5a623', normal: '#00c97d', monitor: '#0097ff' }

export default function AgentTab({ client }) {
  const [memoType, setMemoType] = useState('call')
  const { memoText, memoLoading, memoError, generateMemo, clearMemo,
          isStreaming, streamLogs, streamError, startStream, stopStream,
          runLoading, runResult, triggerRun } = useAgentStore()
  const { refreshAgentLog, refreshMarginCall } = useClientStore()

  const agentLog = client.agentLog || []

  const handleRunAgent = async () => {
    await triggerRun(client.id)
    // Refresh both logs so the UI reflects what the agent did
    await Promise.all([
      refreshAgentLog(client.id),
      refreshMarginCall(client.id)
    ])
  }

  const handleGenerateMemo = () => {
    clearMemo()
    generateMemo(client.id, memoType)
  }

  const actionColors = {
    monitor: '#0097ff', alert: '#f5a623', memo: '#f5a623',
    escalate: '#ff4444', optimize: '#00c97d'
  }

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Run agent */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, padding: 14 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          Agent Controls
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={handleRunAgent}
            disabled={runLoading}
            style={{
              background: runLoading ? 'rgba(0,151,255,0.05)' : 'rgba(0,151,255,0.12)',
              border: '1px solid rgba(0,151,255,0.3)',
              color: '#0097ff',
              borderRadius: 4,
              padding: '7px 14px',
              cursor: runLoading ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: 12
            }}
          >
            {runLoading ? '● Running…' : '▶ Run Agent'}
          </button>

          <button
            onClick={() => isStreaming ? stopStream() : startStream(client.id)}
            style={{
              background: isStreaming ? 'rgba(255,68,68,0.08)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${isStreaming ? 'rgba(255,68,68,0.3)' : 'var(--border)'}`,
              color: isStreaming ? '#ff4444' : 'var(--text-secondary)',
              borderRadius: 4,
              padding: '7px 14px',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: 12
            }}
          >
            {isStreaming ? '■ Stop Stream' : '⟳ Stream Live'}
          </button>
        </div>

        {/* SSE stream log */}
        {(isStreaming || streamLogs.length > 0) && (
          <div style={{
            marginTop: 10,
            background: '#0d1117',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: 10,
            maxHeight: 160,
            overflowY: 'auto',
            fontSize: 11,
            fontFamily: 'var(--font-mono)',
            lineHeight: 1.8
          }}>
            {streamError && <div style={{ color: '#ff4444' }}>{streamError}</div>}
            {streamLogs.map((entry, i) => (
              <div key={i} style={{ color: 'var(--text-secondary)' }}>
                <span style={{ color: '#0097ff' }}>[{entry.node}]</span>{' '}
                <span>{entry.log}</span>
                {entry.mrs_score != null && (
                  <span style={{ color: 'var(--text-muted)' }}> · MRS={entry.mrs_score}</span>
                )}
              </div>
            ))}
            {isStreaming && <div style={{ color: 'var(--text-muted)' }}>● streaming…</div>}
          </div>
        )}

        {/* Run result — shown after a completed agent run (not streaming) */}
        {!runLoading && runResult && !isStreaming && (
          <div style={{ marginTop: 12 }}>
            {/* Header: action tier taken */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
                LAST RUN RESULT
              </span>
              <span style={{
                fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 3,
                background: `${TIER_COLORS[runResult.action_tier] || '#888'}18`,
                color: TIER_COLORS[runResult.action_tier] || '#888',
                border: `1px solid ${TIER_COLORS[runResult.action_tier] || '#888'}40`,
                letterSpacing: '0.05em'
              }}>
                {(runResult.action_tier || 'monitor').toUpperCase()}
              </span>
            </div>

            {/* Agent execution log */}
            {runResult.agent_log?.length > 0 && (
              <div style={{
                background: '#0d1117',
                border: '1px solid var(--border)',
                borderRadius: 4,
                padding: 10,
                maxHeight: 140,
                overflowY: 'auto',
                fontSize: 11,
                fontFamily: 'var(--font-mono)',
                lineHeight: 1.8,
                marginBottom: runResult.memo_draft ? 10 : 0
              }}>
                {runResult.agent_log.map((entry, i) => {
                  const bracket = entry.match(/^\[([^\]]+)\]/)
                  const node = bracket ? bracket[1] : null
                  const rest = bracket ? entry.slice(bracket[0].length).trim() : entry
                  return (
                    <div key={i} style={{ color: 'var(--text-secondary)' }}>
                      {node && <span style={{ color: '#0097ff' }}>[{node}]</span>}{' '}
                      <span>{rest}</span>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Memo draft if generated */}
            {runResult.memo_draft && (
              <AgentMemoBox text={runResult.memo_draft} loading={false} error={null} />
            )}
          </div>
        )}
      </div>

      {/* Memo generator */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, padding: 14 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          Memo Generator
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          {['call', 'advisory'].map(type => (
            <button
              key={type}
              onClick={() => setMemoType(type)}
              style={{
                background: memoType === type ? 'rgba(0,151,255,0.12)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${memoType === type ? 'rgba(0,151,255,0.3)' : 'var(--border)'}`,
                color: memoType === type ? '#0097ff' : 'var(--text-secondary)',
                borderRadius: 4,
                padding: '5px 12px',
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)',
                fontSize: 11
              }}
            >
              {type === 'call' ? 'Margin Call' : 'Advisory'}
            </button>
          ))}
          <button
            onClick={handleGenerateMemo}
            disabled={memoLoading}
            style={{
              marginLeft: 'auto',
              background: memoLoading ? 'rgba(0,201,125,0.04)' : 'rgba(0,201,125,0.12)',
              border: '1px solid rgba(0,201,125,0.3)',
              color: '#00c97d',
              borderRadius: 4,
              padding: '5px 14px',
              cursor: memoLoading ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: 12
            }}
          >
            {memoLoading ? 'Generating…' : 'Generate'}
          </button>
        </div>
        <AgentMemoBox text={memoText} loading={memoLoading} error={memoError} />
      </div>

      {/* Activity log */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, padding: 14 }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          Activity Log
        </div>
        {agentLog.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No agent actions recorded.</div>
        )}
        {agentLog.map((action, i) => (
          <div key={i} style={{
            display: 'flex',
            gap: 10,
            padding: '7px 0',
            borderBottom: '1px solid rgba(255,255,255,0.04)',
            alignItems: 'flex-start'
          }}>
            <span style={{
              fontSize: 10,
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border)',
              borderRadius: 3,
              padding: '2px 6px',
              color: actionColors[action.action_type] || 'var(--text-muted)',
              whiteSpace: 'nowrap'
            }}>
              {action.action_type.toUpperCase()}
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {new Date(action.triggered_at).toLocaleString('en-GB', { timeZone: 'UTC' })} UTC
              </div>
              {action.memo_text && (
                <div style={{
                  fontSize: 11,
                  color: 'var(--text-primary)',
                  marginTop: 3,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }}>
                  {action.memo_text}
                </div>
              )}
            </div>
            <span style={{
              fontSize: 10,
              color: action.status === 'acknowledged' ? '#00c97d' : 'var(--text-muted)'
            }}>
              {action.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
