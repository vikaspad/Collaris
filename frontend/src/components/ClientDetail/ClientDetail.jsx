/**
 * Main client detail panel — tab bar + tab content.
 */
import { useState } from 'react'
import useClientStore from '../../store/clientStore'
import OverviewTab from './OverviewTab'
import CollateralTab from './CollateralTab'
import StressTab from './StressTab'
import MarginCallTab from './MarginCallTab'
import AgentTab from './AgentTab'
import StatusBadge from '../shared/StatusBadge'

const TABS = [
  { id: 'overview',   label: 'Overview' },
  { id: 'collateral', label: 'Collateral' },
  { id: 'stress',     label: 'Stress' },
  { id: 'margincall', label: 'Margin Call' },
  { id: 'agent',      label: 'Agent' }
]

export default function ClientDetail() {
  const { selectedClient, clientLoading } = useClientStore()
  const [activeTab, setActiveTab] = useState('overview')

  if (!selectedClient && !clientLoading) {
    return (
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-muted)', fontSize: 13
      }}>
        Select a client from the sidebar to view details.
      </div>
    )
  }

  if (clientLoading) {
    return (
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-muted)', fontSize: 13, gap: 10
      }}>
        <span className="live-dot" /> Loading client data…
      </div>
    )
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Client header */}
      <div style={{
        padding: '12px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
              {selectedClient.name}
            </h2>
            <StatusBadge status={selectedClient.status} size="sm" />
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
            {selectedClient.id} · {selectedClient.strategy} · AUM ${(selectedClient.aum_millions / 1000).toFixed(2)}B
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border)',
        padding: '0 20px',
        flexShrink: 0
      }}>
        {TABS.map(tab => {
          const hasActiveCall = tab.id === 'margincall' &&
            selectedClient.marginCall?.active_call != null
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid #0097ff' : '2px solid transparent',
                color: activeTab === tab.id ? '#0097ff' : 'var(--text-muted)',
                padding: '10px 16px',
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                letterSpacing: '0.03em',
                transition: 'color 0.15s',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              {tab.label}
              {hasActiveCall && (
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: '#ff4444',
                  boxShadow: '0 0 6px #ff4444',
                  display: 'inline-block'
                }} />
              )}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {activeTab === 'overview'   && <OverviewTab    client={selectedClient} />}
        {activeTab === 'collateral' && <CollateralTab  client={selectedClient} />}
        {activeTab === 'stress'     && <StressTab      client={selectedClient} />}
        {activeTab === 'margincall' && <MarginCallTab  client={selectedClient} />}
        {activeTab === 'agent'      && <AgentTab       client={selectedClient} />}
      </div>
    </div>
  )
}
