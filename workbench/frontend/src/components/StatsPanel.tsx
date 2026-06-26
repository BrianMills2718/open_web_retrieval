import { useState, useEffect } from 'react'
import type { components } from '../types/api'

type ProviderStat = components['schemas']['ProviderStat']

const PROVIDER_COLORS: Record<string, string> = {
  tavily:  '#7c6fef',
  exa:     '#5b9bd5',
  brave:   '#e07c5b',
  searxng: '#6fef9f',
}

export default function StatsPanel() {
  const [stats, setStats] = useState<ProviderStat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/stats')
      .then(r => r.json())
      .then((data: ProviderStat[]) => { setStats(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="empty-state">Loading…</div>
  if (stats.length === 0) return <div className="empty-state">No search calls logged yet.</div>

  const maxCalls = Math.max(...stats.map(s => s.calls), 1)

  return (
    <div className="card">
      <div className="card-title">Provider Activity</div>
      <div className="provider-list">
        {stats.map(s => {
          const color = PROVIDER_COLORS[s.provider] ?? '#888'
          const pct = (s.calls / maxCalls) * 100
          return (
            <div key={s.provider} className="provider-row">
              <span className="provider-name" style={{ color }}>{s.provider}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${pct}%`, background: color }}
                />
              </div>
              <span className="provider-stat">
                {s.calls} call{s.calls !== 1 ? 's' : ''}
                {s.avg_latency_ms != null && (
                  <span style={{ marginLeft: 8, opacity: 0.7 }}>
                    avg {s.avg_latency_ms.toFixed(0)}ms
                  </span>
                )}
                {s.errors > 0 && (
                  <span style={{ marginLeft: 8, color: 'var(--error)' }}>
                    {s.errors} err
                  </span>
                )}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
