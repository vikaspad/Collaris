/**
 * Collateral Optimizer tab — LP recommendations + collateral eligibility matrix.
 */
import UtilBar from '../shared/UtilBar'

function HaircutBadge({ value }) {
  const color = value === 0 ? '#00c97d' : value <= 5 ? '#0097ff' : value <= 12 ? '#f5a623' : '#ff4444'
  return (
    <span style={{ color, fontWeight: 600 }}>{value}%</span>
  )
}

export default function CollateralTab({ client }) {
  const optimize = client.optimize
  const collateral = client.collateral || []

  const summary = optimize?.summary
  const recommendations = optimize?.recommendations || []
  const shortfall = optimize?.shortfall_millions || 0

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Summary cards */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
          {[
            { label: 'Total Collateral', value: `$${summary.total_collateral_mv.toFixed(1)}M` },
            { label: 'Pledged', value: `$${summary.pledged_mv.toFixed(1)}M`, color: '#f5a623' },
            { label: 'Unpledged Eligible', value: `$${summary.unpledged_eligible_mv.toFixed(1)}M`, color: '#00c97d' },
            { label: 'Avg Haircut', value: `${summary.weighted_avg_haircut_pct.toFixed(1)}%` }
          ].map(s => (
            <div key={s.label} style={{
              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              borderRadius: 6, padding: '10px 12px'
            }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{s.label}</div>
              <div style={{ fontSize: 18, fontWeight: 600, color: s.color || 'var(--text-primary)', marginTop: 4 }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Optimizer recommendations */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, padding: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Optimizer Recommendations
          </div>
          {shortfall > 0 && (
            <div style={{ fontSize: 11, color: '#ff4444' }}>
              Shortfall: ${shortfall.toFixed(1)}M
            </div>
          )}
        </div>

        {shortfall === 0 && (
          <div style={{ fontSize: 12, color: '#00c97d', padding: '8px 0' }}>
            No shortfall — portfolio is within margin limits.
          </div>
        )}

        {recommendations.length === 0 && shortfall > 0 && (
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No eligible unpledged assets available.</div>
        )}

        {recommendations.map((rec, i) => (
          <div key={i} style={{
            background: 'rgba(0,151,255,0.06)',
            border: '1px solid rgba(0,151,255,0.2)',
            borderRadius: 4,
            padding: '10px 12px',
            marginBottom: 8,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 500, color: '#0097ff', marginBottom: 2 }}>
                #{i + 1} {rec.action}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                Haircut: {rec.haircut} · MV: ${rec.market_value_millions.toFixed(1)}M
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#00c97d' }}>
                +${rec.frees_millions.toFixed(1)}M
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>freed</div>
            </div>
          </div>
        ))}
      </div>

      {/* Collateral eligibility matrix */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, padding: '14px' }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>
          Collateral Items
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ color: 'var(--text-muted)', fontSize: 10 }}>
              {['Ticker', 'Type', 'Market Value', 'Haircut', 'Pledged', 'Eligible'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '4px 6px', fontWeight: 400, borderBottom: '1px solid var(--border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {collateral.map((item, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <td style={{ padding: '6px 6px', fontWeight: 500 }}>{item.ticker}</td>
                <td style={{ padding: '6px 6px', color: 'var(--text-secondary)', fontSize: 11 }}>
                  {item.asset_type.replace(/_/g, ' ')}
                </td>
                <td style={{ padding: '6px 6px' }}>${item.market_value.toFixed(1)}M</td>
                <td style={{ padding: '6px 6px' }}><HaircutBadge value={item.haircut_pct} /></td>
                <td style={{ padding: '6px 6px' }}>
                  <span style={{ color: item.is_pledged ? '#f5a623' : '#00c97d' }}>
                    {item.is_pledged ? '●' : '○'}
                  </span>
                </td>
                <td style={{ padding: '6px 6px' }}>
                  <span style={{ color: item.eligible ? '#00c97d' : '#ff4444' }}>
                    {item.eligible ? '✓' : '✗'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
