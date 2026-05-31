/**
 * App root — wires together TopBar, Sidebar, StatBar, and ClientDetail.
 * Starts the 30-second risk data polling on mount.
 */
import TopBar from './components/TopBar/TopBar'
import StatBar from './components/StatBar/StatBar'
import Sidebar from './components/Sidebar/Sidebar'
import ClientDetail from './components/ClientDetail/ClientDetail'
import { useRiskData } from './hooks/useRiskData'

export default function App() {
  // Kicks off initial data load + polling
  useRiskData()

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      width: '100vw',
      background: 'var(--bg-base)',
      overflow: 'hidden'
    }}>
      {/* 52px fixed top bar */}
      <TopBar />

      {/* 64px global stats strip */}
      <StatBar />

      {/* Main content row */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 280px sidebar */}
        <Sidebar />

        {/* Flex-1 detail panel */}
        <ClientDetail />
      </div>
    </div>
  )
}
