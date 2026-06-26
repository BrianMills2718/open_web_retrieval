import { useState, useEffect } from 'react'
import type { components } from './types/api'
import RecentCalls from './components/RecentCalls'
import StatsPanel from './components/StatsPanel'

type Tab = 'recent' | 'stats'

const TABS: { id: Tab; label: string }[] = [
  { id: 'recent', label: 'Recent' },
  { id: 'stats', label: 'Stats' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('recent')
  const [health, setHealth] = useState<components['schemas']['HealthResponse'] | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(setHealth)
      .catch(() => null)
  }, [])

  return (
    <div className="workbench-layout">
      <div className="workbench-header">
        <h1>OWR Search Activity</h1>
        {health && (
          <span className="badge badge-accent">
            {health.total_calls.toLocaleString()} calls
          </span>
        )}
        {health && !health.db_exists && (
          <span className="badge" style={{ color: 'var(--error)' }}>DB missing</span>
        )}
      </div>
      <div className="tab-bar">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn${activeTab === t.id ? ' active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="tab-content">
        {activeTab === 'recent' && <RecentCalls />}
        {activeTab === 'stats' && <StatsPanel />}
      </div>
    </div>
  )
}
