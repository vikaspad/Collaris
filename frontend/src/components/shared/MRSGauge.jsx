/**
 * Arc gauge for the Margin Risk Score (0–100).
 * Color transitions from green → amber → red as score rises.
 */
export default function MRSGauge({ value = 0, size = 120 }) {
  const radius = (size - 16) / 2
  const cx = size / 2
  const cy = size / 2

  // Arc spans 240° (from 150° to 30° going clockwise = bottom-left to bottom-right)
  const startAngle = 150
  const endAngle = 30
  const totalDegrees = 240

  // Clamp value to [0, 100]
  const clamped = Math.min(100, Math.max(0, value))
  const filled = (clamped / 100) * totalDegrees

  function polarToXY(angleDeg, r) {
    const rad = (angleDeg - 90) * (Math.PI / 180)
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad)
    }
  }

  function describeArc(startDeg, endDeg, r) {
    const start = polarToXY(startDeg, r)
    const end = polarToXY(endDeg, r)
    const largeArc = endDeg - startDeg > 180 ? 1 : 0
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`
  }

  // Color based on value
  const color = clamped >= 85 ? '#ff4444' : clamped >= 65 ? '#f5a623' : '#00c97d'

  const trackPath = describeArc(startAngle, startAngle + totalDegrees, radius)
  const filledEndAngle = startAngle + filled
  const filledPath = filled > 0 ? describeArc(startAngle, filledEndAngle, radius) : null

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Track */}
      <path
        d={trackPath}
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth={8}
        strokeLinecap="round"
      />
      {/* Filled arc */}
      {filledPath && (
        <path
          d={filledPath}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color}55)` }}
        />
      )}
      {/* Score label */}
      <text
        x={cx} y={cy - 4}
        textAnchor="middle"
        fill={color}
        fontSize={size * 0.22}
        fontWeight={600}
        fontFamily="var(--font-mono)"
      >
        {clamped}
      </text>
      <text
        x={cx} y={cy + size * 0.14}
        textAnchor="middle"
        fill="var(--text-muted)"
        fontSize={size * 0.09}
        fontFamily="var(--font-mono)"
      >
        MRS
      </text>
    </svg>
  )
}
