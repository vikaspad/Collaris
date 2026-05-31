/**
 * Single row in the client list sidebar.
 */
import StatusBadge from '../shared/StatusBadge'
import UtilBar from '../shared/UtilBar'

export default function ClientRow({ client, active, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '10px 14px',
        cursor: 'pointer',
        borderBottom: '1px solid var(--border)',
        background: active ? 'rgba(0,151,255,0.08)' : 'transparent',
        borderLeft: active ? '2px solid #0097ff' : '2px solid transparent',
        transition: 'background 0.15s'
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.3 }}>
            {client.name}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>
            {client.id} · {client.strategy}
          </div>
        </div>
        <StatusBadge status={client.status} size="sm" />
      </div>

      {/* MRS + utilization bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>MRS</div>
        <div style={{
          fontSize: 13, fontWeight: 600,
          color: client.mrs_score >= 85 ? '#ff4444' : client.mrs_score >= 65 ? '#f5a623' : '#00c97d'
        }}>
          {client.mrs_score?.toFixed(0) ?? '—'}
        </div>
        <div style={{ flex: 1 }}>
          <UtilBar value={client.utilization_pct ?? 0} height={4} showLabel={false} />
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
          {client.utilization_pct?.toFixed(1) ?? '—'}%
        </div>
      </div>

      {/* Shortfall if any */}
      {client.shortfall_millions > 0 && (
        <div style={{ fontSize: 10, color: 'var(--status-breach)', marginTop: 2 }}>
          Shortfall: ${client.shortfall_millions.toFixed(1)}M
        </div>
      )}
    </div>
  )
}
