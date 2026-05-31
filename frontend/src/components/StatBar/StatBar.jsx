/**
 * 64px horizontal strip with 5 global risk metrics.
 * Data comes from dashboardSummary in clientStore.
 */
import useClientStore from '../../store/clientStore'

function Stat({ label, value, color }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      padding: '0 24px',
      borderRight: '1px solid var(--border)'
    }}>
      <div style={{ fontSize: 18, fontWeight: 600, color: color || 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
        {value ?? '—'}
      </div>
      <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginTop: 2 }}>
        {label}
      </div>
    </div>
  )
}

export default function StatBar() {
  const { dashboardSummary: s, clients } = useClientStore()

  const totalAUM = clients.reduce((acc, c) => acc + (c.aum_millions || 0), 0)
  const aum = totalAUM > 0 ? `$${(totalAUM / 1000).toFixed(1)}B` : '—'

  return (
    <div style={{
      height: 64,
      borderBottom: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      paddingLeft: 20,
      flexShrink: 0,
      background: 'rgba(255,255,255,0.015)'
    }}>
      <Stat label="Total Clients" value={s?.total_clients ?? clients.length} />
      <Stat
        label="In Breach"
        value={s?.breach_count ?? '—'}
        color={s?.breach_count > 0 ? 'var(--status-breach)' : undefined}
      />
      <Stat
        label="Warning"
        value={s?.warning_count ?? '—'}
        color={s?.warning_count > 0 ? 'var(--status-warning)' : undefined}
      />
      <Stat
        label="Total Shortfall"
        value={s ? `$${s.total_shortfall_millions.toFixed(1)}M` : '—'}
        color={s?.total_shortfall_millions > 0 ? 'var(--status-breach)' : undefined}
      />
      <Stat label="Total AUM" value={aum} />
    </div>
  )
}
