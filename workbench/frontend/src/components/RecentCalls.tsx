import { useState, useEffect } from 'react'
import type { components } from '../types/api'

type Row = components['schemas']['SearchCallRow']

const PROVIDER_COLORS: Record<string, string> = {
  tavily:  '#7c6fef',
  exa:     '#5b9bd5',
  brave:   '#e07c5b',
  searxng: '#6fef9f',
}

function providerBadge(provider: string) {
  const color = PROVIDER_COLORS[provider] ?? '#888'
  return (
    <span
      className="provider-badge"
      style={{ background: color + '22', color, border: `1px solid ${color}55` }}
    >
      {provider}
    </span>
  )
}

function formatTs(ts: string) {
  try {
    const d = new Date(ts)
    return d.toLocaleString('en-US', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts
  }
}

export default function RecentCalls() {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [queryFilter, setQueryFilter] = useState('')
  const [providerFilter, setProviderFilter] = useState('')
  const [errorsOnly, setErrorsOnly] = useState(false)
  const [selected, setSelected] = useState<Row | null>(null)

  useEffect(() => {
    const params = new URLSearchParams({ limit: '200' })
    if (providerFilter) params.set('provider', providerFilter)
    if (errorsOnly) params.set('has_error', 'true')
    setLoading(true)
    fetch(`/api/calls/recent?${params}`)
      .then(r => r.json())
      .then((data: Row[]) => { setRows(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [providerFilter, errorsOnly])

  const providers = Array.from(new Set(rows.map(r => r.provider))).sort()

  const visible = rows.filter(r =>
    !queryFilter || r.query.toLowerCase().includes(queryFilter.toLowerCase())
  )

  return (
    <>
      <div className="filter-bar">
        <input
          type="text"
          placeholder="Filter by query…"
          value={queryFilter}
          onChange={e => setQueryFilter(e.target.value)}
        />
        <select value={providerFilter} onChange={e => setProviderFilter(e.target.value)}>
          <option value="">All providers</option>
          {providers.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13, color: 'var(--muted)' }}>
          <input
            type="checkbox"
            checked={errorsOnly}
            onChange={e => setErrorsOnly(e.target.checked)}
            style={{ width: 'auto', padding: 0 }}
          />
          Errors only
        </label>
        <span style={{ fontSize: 12, color: 'var(--muted)', marginLeft: 'auto' }}>
          {visible.length} row{visible.length !== 1 ? 's' : ''}
        </span>
      </div>

      {loading ? (
        <div className="empty-state">Loading…</div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Query</th>
                <th>Provider</th>
                <th>Latency ms</th>
                <th>Results</th>
                <th>Task</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>No results</td></tr>
              ) : visible.map(row => (
                <tr
                  key={row.id}
                  className="clickable-row"
                  onClick={() => setSelected(row.id === selected?.id ? null : row)}
                >
                  <td style={{ fontSize: 11, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{formatTs(row.timestamp)}</td>
                  <td style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.query}>
                    {row.query.length > 60 ? row.query.slice(0, 60) + '…' : row.query}
                  </td>
                  <td>{providerBadge(row.provider)}</td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {row.latency_ms != null ? row.latency_ms.toFixed(0) : '—'}
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>{row.num_results ?? '—'}</td>
                  <td style={{ fontSize: 11, color: 'var(--muted)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {row.task ?? '—'}
                  </td>
                  <td>
                    {row.error && <span className="status-err" title={row.error}>✕</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <div className="detail-drawer">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <h2>Call #{selected.id}</h2>
            <button onClick={() => setSelected(null)} style={{ fontSize: 18, lineHeight: 1, padding: '0 6px' }}>×</button>
          </div>

          <div className="detail-row">
            <span className="detail-key">Timestamp</span>
            <span className="detail-val">{selected.timestamp}</span>
          </div>
          <div className="detail-row">
            <span className="detail-key">Provider</span>
            <span className="detail-val">{selected.provider}</span>
          </div>
          <div className="detail-row">
            <span className="detail-key">Query</span>
            <span className="detail-val">{selected.query}</span>
          </div>
          <div className="detail-row">
            <span className="detail-key">Latency</span>
            <span className="detail-val">{selected.latency_ms != null ? `${selected.latency_ms}ms` : '—'}</span>
          </div>
          <div className="detail-row">
            <span className="detail-key">Results</span>
            <span className="detail-val">{selected.num_results ?? '—'}</span>
          </div>
          {selected.trace_id && (
            <div className="detail-row">
              <span className="detail-key">Trace ID</span>
              <span className="detail-val">{selected.trace_id}</span>
            </div>
          )}
          {selected.task && (
            <div className="detail-row">
              <span className="detail-key">Task</span>
              <span className="detail-val">{selected.task}</span>
            </div>
          )}
          {selected.error && (
            <div className="detail-row">
              <span className="detail-key" style={{ color: 'var(--error)' }}>Error</span>
              <span className="detail-val" style={{ color: 'var(--error)' }}>{selected.error}</span>
            </div>
          )}
          {selected.top_sources && selected.top_sources.length > 0 && (
            <div className="detail-row">
              <span className="detail-key">Top Sources</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>
                {selected.top_sources.map((url, i) => (
                  <span key={i} className="detail-val" style={{ fontSize: 11 }}>{url}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </>
  )
}
