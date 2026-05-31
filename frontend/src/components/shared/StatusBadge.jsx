/**
 * Colored pill badge for breach / warning / normal status.
 * Rules from CLAUDE.md §12.
 */
export default function StatusBadge({ status, size = 'sm' }) {
  const config = {
    breach:  { label: 'BREACH',  bg: 'rgba(255,68,68,0.15)',   text: '#ff4444', border: 'rgba(255,68,68,0.3)' },
    warning: { label: 'WARNING', bg: 'rgba(245,166,35,0.15)',  text: '#f5a623', border: 'rgba(245,166,35,0.3)' },
    normal:  { label: 'NORMAL',  bg: 'rgba(0,201,125,0.12)',   text: '#00c97d', border: 'rgba(0,201,125,0.3)' }
  }
  const c = config[status] || config.normal
  const padding = size === 'sm' ? '2px 7px' : '4px 12px'
  const fontSize = size === 'sm' ? '10px' : '12px'

  return (
    <span style={{
      display: 'inline-block',
      background: c.bg,
      color: c.text,
      border: `1px solid ${c.border}`,
      borderRadius: '3px',
      padding,
      fontSize,
      fontWeight: 600,
      letterSpacing: '0.06em',
      fontFamily: 'var(--font-mono)'
    }}>
      {c.label}
    </span>
  )
}
