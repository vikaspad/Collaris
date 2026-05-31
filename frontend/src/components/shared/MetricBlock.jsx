/**
 * Grey metric card — label + value + optional sub-label.
 * Used in the Overview tab's 6-metric grid.
 */
export default function MetricBlock({ label, value, sub, color }) {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 6,
      padding: '12px 14px',
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }}>
      <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {label}
      </div>
      <div style={{
        fontSize: 22,
        fontWeight: 600,
        color: color || 'var(--text-primary)',
        lineHeight: 1.2,
        fontFamily: 'var(--font-mono)'
      }}>
        {value ?? '—'}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{sub}</div>
      )}
    </div>
  )
}
