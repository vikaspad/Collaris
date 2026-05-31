/**
 * Stress Scenarios tab — 4 scenarios with projected utilization bars.
 */
import UtilBar from '../shared/UtilBar'

const SCENARIO_ORDER = ['covid_2020', 'rate_spike_2022', 'svb_2023', 'custom_equity_10']

export default function StressTab({ client }) {
  const results = client.stressResults || []

  // Sort by scenario order
  const ordered = SCENARIO_ORDER
    .map(id => results.find(r => r.scenario_id === id))
    .filter(Boolean)

  if (ordered.length === 0) {
    return (
      <div className="fade-in" style={{ color: 'var(--text-muted)', padding: '20px 0', fontSize: 12 }}>
        No stress results available. Select a client to load scenarios.
      </div>
    )
  }

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
        Showing projected utilization and NAV impact under each historical scenario.
      </div>

      {ordered.map((r, i) => {
        const isWorst = r.stressed_utilization >= 85
        const borderColor = isWorst ? 'rgba(255,68,68,0.3)' : 'var(--border)'

        return (
          <div key={i} style={{
            background: 'var(--bg-elevated)',
            border: `1px solid ${borderColor}`,
            borderRadius: 6,
            padding: '14px'
          }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                {r.scenario_label}
              </div>
              {isWorst && (
                <span style={{
                  fontSize: 10, background: 'rgba(255,68,68,0.15)',
                  color: '#ff4444', border: '1px solid rgba(255,68,68,0.3)',
                  borderRadius: 3, padding: '2px 6px', letterSpacing: '0.06em'
                }}>
                  BREACH
                </span>
              )}
            </div>

            {/* Utilization comparison */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 4 }}>Base Utilization</div>
                <UtilBar value={r.base_utilization} height={6} showLabel={false} />
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 3 }}>{r.base_utilization.toFixed(1)}%</div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 4 }}>Stressed Utilization</div>
                <UtilBar value={r.stressed_utilization} height={6} showLabel={false} />
                <div style={{ fontSize: 11, color: isWorst ? '#ff4444' : 'var(--text-secondary)', marginTop: 3 }}>
                  {r.stressed_utilization.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* NAV impact */}
            <div style={{ display: 'flex', gap: 20, fontSize: 12 }}>
              <div>
                <span style={{ color: 'var(--text-muted)', marginRight: 6 }}>Base NAV</span>
                <span style={{ color: 'var(--text-primary)' }}>${r.base_nav.toFixed(1)}M</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', marginRight: 6 }}>Stressed NAV</span>
                <span style={{ color: r.stressed_nav < r.base_nav ? '#ff4444' : '#00c97d' }}>
                  ${r.stressed_nav.toFixed(1)}M
                </span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', marginRight: 6 }}>Impact</span>
                <span style={{ color: r.nav_change_millions < 0 ? '#ff4444' : '#00c97d', fontWeight: 600 }}>
                  {r.nav_change_millions >= 0 ? '+' : ''}{r.nav_change_millions.toFixed(1)}M
                  ({r.nav_change_pct >= 0 ? '+' : ''}{r.nav_change_pct.toFixed(1)}%)
                </span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
