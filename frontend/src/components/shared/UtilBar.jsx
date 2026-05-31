/**
 * Thin horizontal utilization progress bar with optional glow at high values.
 */
export default function UtilBar({ value = 0, height = 6, showLabel = true }) {
  const clamped = Math.min(100, Math.max(0, value))
  const color = clamped >= 85 ? '#ff4444' : clamped >= 65 ? '#f5a623' : '#00c97d'
  const glow = clamped >= 65 ? `0 0 6px ${color}66` : 'none'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {showLabel && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-secondary)' }}>
          <span>Utilization</span>
          <span style={{ color, fontWeight: 600 }}>{clamped.toFixed(1)}%</span>
        </div>
      )}
      <div style={{
        width: '100%',
        height,
        background: 'rgba(255,255,255,0.07)',
        borderRadius: height / 2,
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${clamped}%`,
          height: '100%',
          background: color,
          borderRadius: height / 2,
          boxShadow: glow,
          transition: 'width 0.4s ease'
        }} />
      </div>
    </div>
  )
}
