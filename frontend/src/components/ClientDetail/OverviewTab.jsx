/**
 * Overview tab — 6 metric blocks, utilization sparkline, top holdings, risk narrative.
 */
import MRSGauge from '../shared/MRSGauge'
import UtilBar from '../shared/UtilBar'
import MetricBlock from '../shared/MetricBlock'
import Sparkline from '../shared/Sparkline'
import StatusBadge from '../shared/StatusBadge'

export default function OverviewTab({ client }) {
  const r = client.latest_risk
  const p = client.latest_portfolio
  const history = client.history || []
  const positions = p?.positions || []

  // Sort positions by abs market value for top holdings
  const topHoldings = [...positions]
    .sort((a, b) => Math.abs(b.market_value) - Math.abs(a.market_value))
    .slice(0, 5)

  const statusColor = {
    breach: '#ff4444', warning: '#f5a623', normal: '#00c97d'
  }[client.status] || 'var(--text-primary)'

  const trendArrow = { up: '↑', down: '↓', stable: '→' }[r?.trend] || '→'
  const trendColor = { up: '#ff4444', down: '#00c97d', stable: 'var(--text-muted)' }[r?.trend]

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Hero row: MRS gauge + key stats */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          minWidth: 140
        }}>
          <MRSGauge value={r?.mrs_score ?? 0} size={110} />
          <StatusBadge status={client.status} size="md" />
        </div>

        {/* 6 metric blocks */}
        <div style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 8
        }}>
          <MetricBlock
            label="NAV"
            value={p ? `$${p.nav.toFixed(1)}M` : '—'}
            sub="Net Asset Value"
          />
          <MetricBlock
            label="Gross Exposure"
            value={p ? `$${p.gross_exposure.toFixed(0)}M` : '—'}
            sub={p ? `${((p.gross_exposure / p.nav) * 100).toFixed(0)}% of NAV` : ''}
          />
          <MetricBlock
            label="VaR (1D)"
            value={r ? `$${r.var_1d.toFixed(1)}M` : '—'}
            sub="99% confidence"
            color={r?.var_1d > 50 ? '#f5a623' : undefined}
          />
          <MetricBlock
            label="Shortfall"
            value={r?.shortfall_millions > 0 ? `$${r.shortfall_millions.toFixed(1)}M` : '$0M'}
            color={r?.shortfall_millions > 0 ? '#ff4444' : '#00c97d'}
            sub={r?.shortfall_millions > 0 ? 'Above threshold' : 'No shortfall'}
          />
          <MetricBlock
            label="Lead Time"
            value={r?.lead_time_hours === 0 ? 'BREACH' : r ? `${r.lead_time_hours.toFixed(1)}h` : '—'}
            sub="Est. time to breach"
            color={r?.lead_time_hours < 4 ? '#ff4444' : r?.lead_time_hours < 24 ? '#f5a623' : undefined}
          />
          <MetricBlock
            label="AUM"
            value={`$${(client.aum_millions / 1000).toFixed(2)}B`}
            sub={client.strategy}
          />
        </div>
      </div>

      {/* Utilization bar + trend */}
      {r && (
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '12px 14px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Margin Utilization
            </span>
            <span style={{ fontSize: 11, color: trendColor }}>
              {trendArrow} {r.trend}
            </span>
          </div>
          <UtilBar value={r.utilization_pct} height={8} showLabel={false} />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 11 }}>
            <span style={{ color: 'var(--text-muted)' }}>
              Margin Used: ${p?.margin_used.toFixed(1)}M
            </span>
            <span style={{ color: statusColor, fontWeight: 600 }}>
              {r.utilization_pct.toFixed(1)}%
            </span>
            <span style={{ color: 'var(--text-muted)' }}>
              Available: ${p?.margin_available.toFixed(1)}M
            </span>
          </div>
        </div>
      )}

      {/* MRS trend sparkline */}
      {history.length > 1 && (
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '12px 14px'
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
            MRS Trend (30d)
          </div>
          <Sparkline
            data={history}
            dataKey="mrs_score"
            color={r?.mrs_score >= 85 ? '#ff4444' : r?.mrs_score >= 65 ? '#f5a623' : '#0097ff'}
            height={50}
          />
        </div>
      )}

      {/* Top holdings table */}
      {topHoldings.length > 0 && (
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '12px 14px'
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
            Top Holdings
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ color: 'var(--text-muted)', fontSize: 10 }}>
                {['Ticker', 'Class', 'Direction', 'Market Value'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '4px 0', fontWeight: 400, borderBottom: '1px solid var(--border)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {topHoldings.map((pos, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '5px 0', fontWeight: 500, color: 'var(--text-primary)' }}>{pos.ticker}</td>
                  <td style={{ padding: '5px 0', color: 'var(--text-secondary)' }}>{pos.asset_class}</td>
                  <td style={{ padding: '5px 0' }}>
                    <span style={{ color: pos.direction === 'long' ? '#00c97d' : '#ff4444' }}>
                      {pos.direction}
                    </span>
                  </td>
                  <td style={{ padding: '5px 0', textAlign: 'right', color: pos.market_value < 0 ? '#ff4444' : 'var(--text-primary)' }}>
                    ${Math.abs(pos.market_value).toFixed(1)}M
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
