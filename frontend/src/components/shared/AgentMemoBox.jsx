/**
 * Dark code-style box for displaying LLM-generated memo text.
 */
export default function AgentMemoBox({ text, loading, error }) {
  return (
    <div style={{
      background: '#0d1117',
      border: '1px solid var(--border)',
      borderRadius: 6,
      padding: 16,
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
      lineHeight: 1.7,
      color: 'var(--text-primary)',
      minHeight: 120,
      position: 'relative',
      whiteSpace: 'pre-wrap'
    }}>
      {loading && (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="live-dot" style={{ width: 6, height: 6 }} />
          Generating memo…
        </div>
      )}
      {error && (
        <div style={{ color: 'var(--status-breach)' }}>Error: {error}</div>
      )}
      {!loading && !error && !text && (
        <div style={{ color: 'var(--text-muted)' }}>No memo generated yet. Click Generate to draft one.</div>
      )}
      {!loading && !error && text && text}
    </div>
  )
}
