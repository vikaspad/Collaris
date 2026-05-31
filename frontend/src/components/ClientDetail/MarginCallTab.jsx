import { useState, useEffect } from 'react'
import useClientStore from '../../store/clientStore'
import { acknowledgeMarginCall, resolveMarginCall } from '../../api/client'

// ── Countdown timer (live seconds until due_by) ───────────────────────────────
function CountdownTimer({ dueByIso }) {
  const [remaining, setRemaining] = useState('')
  const [urgent, setUrgent] = useState(false)

  useEffect(() => {
    if (!dueByIso) return
    const due = new Date(dueByIso)
    const tick = () => {
      const diff = Math.max(0, due - Date.now())
      const totalSecs = Math.floor(diff / 1000)
      const h = Math.floor(totalSecs / 3600)
      const m = Math.floor((totalSecs % 3600) / 60)
      const s = totalSecs % 60
      setUrgent(totalSecs < 1800)
      setRemaining(h > 0 ? `${h}h ${m}m ${s}s` : `${m}m ${s}s`)
    }
    tick()
    const t = setInterval(tick, 1000)
    return () => clearInterval(t)
  }, [dueByIso])

  return (
    <span style={{
      fontFamily: 'var(--font-mono)',
      fontWeight: 700,
      fontSize: 20,
      color: urgent ? '#ff4444' : '#f5a623',
      textShadow: urgent ? '0 0 12px #ff444455' : 'none'
    }}>
      {remaining || '—'}
    </span>
  )
}

// ── Shared style helpers ──────────────────────────────────────────────────────
const card = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border)',
  borderRadius: 8,
  padding: 20,
  marginBottom: 16
}
const sectionTitle = {
  fontSize: 10,
  color: 'var(--text-muted)',
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  marginBottom: 14
}
const metricBox = {
  background: 'rgba(255,255,255,0.02)',
  border: '1px solid rgba(255,255,255,0.05)',
  borderRadius: 6,
  padding: '12px 14px'
}

function btn(variant) {
  const variants = {
    red:   { bg: 'rgba(255,68,68,0.12)',  border: 'rgba(255,68,68,0.3)',   color: '#ff4444' },
    blue:  { bg: 'rgba(0,151,255,0.12)', border: 'rgba(0,151,255,0.3)',  color: '#0097ff' },
    green: { bg: 'rgba(0,201,125,0.12)', border: 'rgba(0,201,125,0.3)', color: '#00c97d' },
    ghost: { bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary)' }
  }
  const v = variants[variant] || variants.ghost
  return {
    padding: '6px 14px',
    borderRadius: 5,
    border: `1px solid ${v.border}`,
    background: v.bg,
    color: v.color,
    cursor: 'pointer',
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: '0.05em'
  }
}

const COMMS_COLORS = { issued: '#ff4444', notified: '#0097ff', ack: '#00c97d', escalated: '#f5a623' }
const COMMS_LABELS = { issued: 'ISSUED', notified: 'SENT', ack: 'ACK', escalated: 'ESCALATED' }

// ── No active call state ─────────────────────────────────────────────────────
function NoActiveCall({ history, clientName, utilization }) {
  return (
    <>
      <div style={{ ...card, textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: 28, marginBottom: 10, color: '#00c97d' }}>✓</div>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#00c97d', marginBottom: 6 }}>
          No Active Margin Calls
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {clientName} has no outstanding calls. Utilization is within safe parameters at {utilization?.toFixed(1)}%.
        </div>
      </div>
      {history && history.length > 0 && <CallHistoryTable history={history} />}
    </>
  )
}

// ── Call history table ────────────────────────────────────────────────────────
function CallHistoryTable({ history }) {
  const headers = ['Date', 'Call ID', 'Shortfall', 'Type', 'Resolved In', 'Resolution']
  const cols = '0.8fr 1.3fr 0.8fr 0.9fr 1fr 1fr'
  const totalShortfall = history.reduce((a, h) => a + (h.shortfall || 0), 0)

  return (
    <div style={card}>
      <div style={sectionTitle}>Call History — Last 30 Days ({history.length} calls)</div>
      <div style={{ display: 'grid', gridTemplateColumns: cols, marginBottom: 8 }}>
        {headers.map(h => (
          <span key={h} style={{ fontSize: 9, color: 'rgba(255,255,255,0.2)', letterSpacing: '0.08em',
            paddingBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{h}</span>
        ))}
      </div>
      {history.map((h, i) => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: cols, padding: '9px 0',
          borderBottom: '1px solid rgba(255,255,255,0.04)', alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{h.date}</span>
          <span style={{ fontSize: 10, color: '#7ab3d4', fontFamily: 'var(--font-mono)' }}>{h.call_id}</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: '#ff4444' }}>${h.shortfall}M</span>
          <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{h.type}</span>
          <span style={{ fontSize: 11, color: 'var(--text-primary)' }}>{h.resolved_in}</span>
          <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 3,
            background: 'rgba(0,201,125,0.08)', color: '#00c97d', display: 'inline-block' }}>
            {h.resolution}
          </span>
        </div>
      ))}
      <div style={{ marginTop: 14, display: 'flex', gap: 28 }}>
        <div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>TOTAL SHORTFALL (30D)</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#ff4444', marginTop: 2 }}>
            ${totalShortfall.toFixed(1)}M
          </div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>CALLS</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
            {history.length}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main tab component ────────────────────────────────────────────────────────
export default function MarginCallTab({ client }) {
  const { refreshMarginCall } = useClientStore()
  const [selectedRes, setSelectedRes] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const data = client.marginCall
  const risk = client.latest_risk

  // Loading state
  if (data === undefined) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: 200, color: 'var(--text-muted)', fontSize: 12 }}>
        Loading margin call data…
      </div>
    )
  }

  // No active call
  if (!data || !data.active_call) {
    return (
      <NoActiveCall
        history={data?.history || []}
        clientName={client.name}
        utilization={risk?.utilization_pct}
      />
    )
  }

  const call = data.active_call
  const positionBreakdown = data.position_breakdown || []
  const resolutionOptions = data.resolution_options || []
  const commsLog = data.comms_log || []
  const consequences = data.consequences || []
  const history = data.history || []

  const handleAcknowledge = async () => {
    setActionLoading(true)
    try {
      await acknowledgeMarginCall(client.id, call.id)
      await refreshMarginCall(client.id)
    } finally {
      setActionLoading(false)
    }
  }

  const handleResolve = async (resolutionType) => {
    setActionLoading(true)
    try {
      await resolveMarginCall(client.id, call.id, resolutionType)
      await refreshMarginCall(client.id)
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="fade-in">

      {/* ── Active Call Banner ── */}
      <div style={{
        background: 'rgba(255,68,68,0.05)',
        border: '1px solid rgba(255,68,68,0.2)',
        borderRadius: 8,
        padding: 20,
        marginBottom: 16
      }}>
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 9, background: '#ff4444', color: '#fff',
            padding: '3px 8px', borderRadius: 3, fontWeight: 700, letterSpacing: '0.06em' }}>
            ACTIVE
          </span>
          <span style={{ fontSize: 11, color: '#ff4444', fontWeight: 700 }}>
            {call.type?.toUpperCase()} — {call.call_id}
          </span>
          <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto' }}>
            {call.regulation}
          </span>
        </div>

        {/* Metrics row */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
          <div style={{ ...metricBox, flex: '1 1 120px' }}>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>SHORTFALL</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: '#ff4444', marginTop: 2 }}>
              ${call.shortfall_millions}M
            </div>
          </div>
          <div style={{ ...metricBox, flex: '1 1 120px' }}>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>ISSUED AT</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              {call.issued_at}
            </div>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>{call.issued_by}</div>
          </div>
          <div style={{ ...metricBox, flex: '1 1 120px' }}>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>ACKNOWLEDGED</div>
            <div style={{ fontSize: 13, fontWeight: 700, marginTop: 4,
              color: call.acknowledged_at ? '#00c97d' : '#ff4444' }}>
              {call.acknowledged_at ? `✓ ${call.acknowledged_at}` : '✗ Pending'}
            </div>
          </div>
          <div style={{ ...metricBox, flex: '1 1 140px', textAlign: 'right' }}>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: 6 }}>
              TIME REMAINING
            </div>
            <CountdownTimer dueByIso={call.due_by_iso} />
            <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4 }}>
              Due by {call.due_by}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button style={btn('green')} disabled={actionLoading} onClick={handleAcknowledge}>
            ✓ {actionLoading ? 'Processing…' : 'Acknowledge'}
          </button>
          <button style={btn('green')} disabled={actionLoading}
            onClick={() => handleResolve('deposit')}>
            ✓ Mark Resolved
          </button>
          <button style={btn('blue')}>↩ Re-send Notice</button>
          <button style={btn('red')}>⚡ Escalate to Desk</button>
          <button style={btn('ghost')}>⬇ Download PDF</button>
        </div>
      </div>

      {/* ── Position-Level Breakdown ── */}
      {positionBreakdown.length > 0 && (
        <div style={card}>
          <div style={sectionTitle}>Position-Level Shortfall Breakdown</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr 1fr 1fr 1fr', marginBottom: 8 }}>
            {['Ticker', 'Mkt Value', 'Margin Req', 'Excess / (Deficit)', 'Contribution'].map((h, i) => (
              <span key={i} style={{ fontSize: 9, color: 'rgba(255,255,255,0.2)', letterSpacing: '0.08em',
                paddingBottom: 8, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{h}</span>
            ))}
          </div>
          {positionBreakdown.map((p, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr 1fr 1fr 1fr',
              padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{p.ticker}</span>
                <span style={{
                  fontSize: 9, marginLeft: 6,
                  color: p.direction === 'long' ? '#00c97d' : '#f5a623',
                  background: p.direction === 'long' ? 'rgba(0,201,125,0.1)' : 'rgba(245,166,35,0.1)',
                  padding: '1px 5px', borderRadius: 3
                }}>
                  {p.direction?.toUpperCase()}
                </span>
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>${p.market_value}M</span>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>${p.margin_req}M</span>
              <span style={{ fontSize: 11, fontWeight: 700, color: p.excess < 0 ? '#ff4444' : '#00c97d' }}>
                {p.excess < 0 ? `($${Math.abs(p.excess).toFixed(2)}M)` : `+$${p.excess.toFixed(2)}M`}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ flex: 1, height: 3, background: 'rgba(255,255,255,0.05)', borderRadius: 2 }}>
                  <div style={{
                    width: `${p.contribution_pct}%`, height: '100%', borderRadius: 2,
                    background: p.contribution_pct > 25 ? '#ff4444' : '#f5a623'
                  }} />
                </div>
                <span style={{ fontSize: 9, color: 'var(--text-muted)', width: 28, textAlign: 'right' }}>
                  {p.contribution_pct}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Resolution Pathways ── */}
      {resolutionOptions.length > 0 && (
        <div style={card}>
          <div style={sectionTitle}>Resolution Pathways</div>
          {resolutionOptions.map((r, i) => (
            <div key={i}
              onClick={() => setSelectedRes(selectedRes === i ? null : i)}
              style={{
                background: selectedRes === i ? 'rgba(0,151,255,0.06)' : 'rgba(255,255,255,0.02)',
                border: `1px solid ${selectedRes === i ? 'rgba(0,151,255,0.3)' : 'rgba(255,255,255,0.06)'}`,
                borderRadius: 6,
                padding: '14px 16px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                marginBottom: 8
              }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
                    {String.fromCharCode(65 + i)}. {r.type}
                  </span>
                  <span style={{
                    fontSize: 9, padding: '2px 7px', borderRadius: 3,
                    background: r.feasibility === 'High' ? 'rgba(0,201,125,0.1)'
                      : r.feasibility === 'Medium' ? 'rgba(245,166,35,0.1)' : 'rgba(255,68,68,0.1)',
                    color: r.feasibility === 'High' ? '#00c97d'
                      : r.feasibility === 'Medium' ? '#f5a623' : '#ff4444'
                  }}>
                    {r.feasibility} Feasibility
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 15, fontWeight: 800, color: '#00c97d' }}>${r.amount}M</div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>Settle {r.time_to_settle}</div>
                </div>
              </div>
              {selectedRes === i && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: 11, color: '#7ab3d4', marginBottom: 10, lineHeight: 1.6 }}>
                    {r.notes}
                  </div>
                  <button style={btn('green')}
                    onClick={(e) => { e.stopPropagation(); handleResolve(r.type.toLowerCase().replace(' ', '_')) }}>
                    ✓ Initiate {r.type}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Comms Log + Consequences ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Comms log */}
        <div style={card}>
          <div style={sectionTitle}>Communications Log</div>
          {commsLog.map((entry, i) => (
            <div key={i} style={{ display: 'flex', gap: 10, padding: '8px 0',
              borderBottom: '1px solid rgba(255,255,255,0.04)', alignItems: 'flex-start' }}>
              <span style={{ fontSize: 9, color: 'var(--text-muted)', width: 36, flexShrink: 0, marginTop: 1 }}>
                {entry.time}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {entry.event}
                </div>
                <span style={{ fontSize: 8, color: 'var(--text-muted)', marginTop: 2, display: 'block' }}>
                  {entry.actor}
                </span>
              </div>
              <span style={{
                fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 3, flexShrink: 0,
                background: `${COMMS_COLORS[entry.type] || '#888'}20`,
                color: COMMS_COLORS[entry.type] || '#888',
                letterSpacing: '0.04em'
              }}>
                {COMMS_LABELS[entry.type] || entry.type?.toUpperCase()}
              </span>
            </div>
          ))}
          {commsLog.length === 0 && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>No comms recorded yet.</div>
          )}
        </div>

        {/* Consequence timeline */}
        <div style={card}>
          <div style={sectionTitle}>Consequence Timeline — If Unresolved</div>
          {consequences.map((c, i) => (
            <div key={i} style={{ display: 'flex', gap: 10, padding: '10px 0',
              borderBottom: '1px solid rgba(255,255,255,0.04)', alignItems: 'flex-start' }}>
              <div style={{
                width: 8, height: 8, borderRadius: '50%', marginTop: 4, flexShrink: 0,
                background: c.severity === 'high' ? '#ff4444' : '#f5a623',
                boxShadow: `0 0 6px ${c.severity === 'high' ? '#ff4444' : '#f5a623'}`
              }} />
              <div>
                <div style={{ fontSize: 9, fontWeight: 700, marginBottom: 3, letterSpacing: '0.04em',
                  color: c.severity === 'high' ? '#ff4444' : '#f5a623' }}>
                  {c.time}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {c.event}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Call History ── */}
      {history.length > 0 && <CallHistoryTable history={history} />}
    </div>
  )
}
