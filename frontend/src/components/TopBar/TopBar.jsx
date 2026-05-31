/**
 * Fixed 52px top bar — logo left, live indicator + clock right.
 */
import { useState, useEffect } from 'react'

export default function TopBar() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const formatted = time.toLocaleTimeString('en-GB', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'UTC'
  }) + ' UTC'

  return (
    <div style={{
      height: 52,
      borderBottom: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      flexShrink: 0,
      background: 'var(--bg-base)'
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 28, height: 28,
          background: 'rgba(0,151,255,0.15)',
          border: '1px solid rgba(0,151,255,0.4)',
          borderRadius: 4,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, color: '#0097ff'
        }}>
          C
        </div>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
            COLLARIS
          </div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.12em', marginTop: -2 }}>
            MARGIN INTELLIGENCE
          </div>
        </div>
      </div>

      {/* Right section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="live-dot" />
          <span style={{ fontSize: 11, color: 'var(--status-normal)', letterSpacing: '0.05em' }}>LIVE</span>
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', letterSpacing: '0.02em' }}>
          {formatted}
        </div>
      </div>
    </div>
  )
}
