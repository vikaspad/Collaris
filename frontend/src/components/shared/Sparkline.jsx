/**
 * Minimal 7-point trend sparkline using Recharts.
 * Expects data as [{ date, mrs_score, utilization_pct }].
 */
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'

export default function Sparkline({ data = [], dataKey = 'mrs_score', color = '#0097ff', height = 40 }) {
  if (!data || data.length < 2) {
    return <div style={{ height, display: 'flex', alignItems: 'center', color: 'var(--text-muted)', fontSize: 11 }}>—</div>
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            fontSize: 11,
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-primary)'
          }}
          formatter={(val) => [val?.toFixed(1), dataKey === 'mrs_score' ? 'MRS' : 'Util%']}
          labelFormatter={() => ''}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
