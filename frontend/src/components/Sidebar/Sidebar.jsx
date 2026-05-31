/**
 * 280px fixed sidebar — client list with filter tabs and search.
 */
import { useEffect } from 'react'
import useClientStore from '../../store/clientStore'
import ClientRow from './ClientRow'

const FILTER_TABS = ['all', 'breach', 'warning', 'normal']

export default function Sidebar() {
  const {
    clientsLoading, clientsError,
    selectedClientId, selectClient,
    filterStatus, setFilter,
    searchQuery, setSearch,
    getFilteredClients
  } = useClientStore()

  const filtered = getFilteredClients()

  const tabColor = (tab) => {
    if (tab === 'breach') return '#ff4444'
    if (tab === 'warning') return '#f5a623'
    if (tab === 'normal') return '#00c97d'
    return 'var(--text-secondary)'
  }

  return (
    <div style={{
      width: 280,
      flexShrink: 0,
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: 'var(--bg-base)'
    }}>
      {/* Search */}
      <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border)' }}>
        <input
          placeholder="Search clients…"
          value={searchQuery}
          onChange={e => setSearch(e.target.value)}
          style={{
            width: '100%',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '6px 10px',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            outline: 'none'
          }}
        />
      </div>

      {/* Filter tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border)',
        padding: '0 4px'
      }}>
        {FILTER_TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            style={{
              flex: 1,
              background: 'none',
              border: 'none',
              borderBottom: filterStatus === tab ? `2px solid ${tabColor(tab)}` : '2px solid transparent',
              color: filterStatus === tab ? tabColor(tab) : 'var(--text-muted)',
              padding: '8px 0',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              transition: 'color 0.15s'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Client list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {clientsLoading && (
          <div style={{ padding: 20, color: 'var(--text-muted)', fontSize: 12 }}>Loading clients…</div>
        )}
        {clientsError && (
          <div style={{ padding: 20, color: 'var(--status-breach)', fontSize: 12 }}>{clientsError}</div>
        )}
        {!clientsLoading && filtered.map(client => (
          <ClientRow
            key={client.id}
            client={client}
            active={client.id === selectedClientId}
            onClick={() => selectClient(client.id)}
          />
        ))}
        {!clientsLoading && filtered.length === 0 && !clientsError && (
          <div style={{ padding: 20, color: 'var(--text-muted)', fontSize: 12 }}>No clients match filter.</div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        padding: '8px 14px',
        borderTop: '1px solid var(--border)',
        fontSize: 10,
        color: 'var(--text-muted)'
      }}>
        {filtered.length} client{filtered.length !== 1 ? 's' : ''}
      </div>
    </div>
  )
}
