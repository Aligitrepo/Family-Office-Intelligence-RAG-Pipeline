import React from 'react'
import { Database, Globe, TrendingUp, Users } from 'lucide-react'

const s = {
  panel: {
    background: 'var(--card-bg)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '20px',
    backdropFilter: 'blur(8px)',
  },
  title: {
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: 'var(--gold)',
    marginBottom: '16px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
    marginBottom: '16px',
  },
  stat: {
    background: 'rgba(15,31,61,0.6)',
    borderRadius: '8px',
    padding: '12px',
    border: '1px solid rgba(201,168,76,0.1)',
  },
  statNum: {
    fontSize: '26px',
    fontWeight: 700,
    color: 'var(--gold-light)',
    lineHeight: 1.1,
  },
  statLabel: {
    fontSize: '11px',
    color: 'var(--slate)',
    marginTop: '2px',
  },
  section: {
    marginTop: '14px',
  },
  sectionTitle: {
    fontSize: '11px',
    color: 'var(--slate)',
    marginBottom: '8px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  },
  bar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '5px',
    fontSize: '12px',
  },
  barLabel: { width: '90px', color: 'var(--slate-light)', flexShrink: 0 },
  barTrack: {
    flex: 1,
    height: '6px',
    background: 'rgba(255,255,255,0.08)',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  barFill: (pct, color) => ({
    height: '100%',
    width: `${pct}%`,
    background: color,
    borderRadius: '3px',
    transition: 'width 0.6s ease',
  }),
  barCount: { width: '30px', textAlign: 'right', color: 'var(--slate)', fontSize: '11px' },
  badge: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '10px',
    fontWeight: 600,
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
  },
  model: {
    marginTop: '14px',
    padding: '10px',
    background: 'rgba(15,31,61,0.5)',
    borderRadius: '6px',
    fontSize: '11px',
    color: 'var(--slate)',
    borderLeft: '2px solid var(--gold)',
  },
}

export default function StatsPanel({ stats, loading }) {
  if (loading) {
    return (
      <div style={s.panel}>
        <div style={s.title}><Database size={13} /> Dataset Stats</div>
        <div style={{ color: 'var(--slate)', fontSize: '13px' }}>Loading…</div>
      </div>
    )
  }
  if (!stats) return null

  const total = stats.total_records
  const typeColors = { SFO: '#c9a84c', MFO: '#5b9bd5', VFO: '#6ab187', Unknown: '#8fa3c0' }
  const confColors = { H: '#6ab187', M: '#e8c97a' }

  const topCountries = Object.entries(stats.top_countries || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)

  return (
    <div style={s.panel}>
      <div style={s.title}><Database size={13} /> Dataset Intelligence</div>

      <div style={s.grid}>
        <div style={s.stat}>
          <div style={s.statNum}>{total}</div>
          <div style={s.statLabel}>Validated FOs</div>
        </div>
        <div style={s.stat}>
          <div style={s.statNum}>{Object.keys(stats.top_countries || {}).length}</div>
          <div style={s.statLabel}>Countries</div>
        </div>
        <div style={s.stat}>
          <div style={s.statNum}>{stats.with_aum}</div>
          <div style={s.statLabel}>With AUM data</div>
        </div>
        <div style={s.stat}>
          <div style={s.statNum}>{stats.with_decision_maker}</div>
          <div style={s.statLabel}>With DMs</div>
        </div>
      </div>

      {/* FO Type breakdown */}
      <div style={s.section}>
        <div style={s.sectionTitle}>By Type</div>
        {Object.entries(stats.fo_types || {}).map(([type, count]) => (
          <div key={type} style={s.bar}>
            <div style={s.barLabel}>{type}</div>
            <div style={s.barTrack}>
              <div style={s.barFill(Math.round((count / total) * 100), typeColors[type] || '#8fa3c0')} />
            </div>
            <div style={s.barCount}>{count}</div>
          </div>
        ))}
      </div>

      {/* Confidence */}
      <div style={s.section}>
        <div style={s.sectionTitle}>Confidence</div>
        {Object.entries(stats.confidence || {}).map(([conf, count]) => (
          <div key={conf} style={s.bar}>
            <div style={s.barLabel}>{conf === 'H' ? 'High' : 'Medium'}</div>
            <div style={s.barTrack}>
              <div style={s.barFill(Math.round((count / total) * 100), confColors[conf] || '#8fa3c0')} />
            </div>
            <div style={s.barCount}>{count}</div>
          </div>
        ))}
      </div>

      {/* Top countries */}
      <div style={s.section}>
        <div style={s.sectionTitle}><Globe size={10} style={{ display: 'inline', marginRight: 4 }} />Top Countries</div>
        {topCountries.map(([country, count]) => (
          <div key={country} style={s.bar}>
            <div style={{ ...s.barLabel, width: '110px' }}>{country}</div>
            <div style={s.barTrack}>
              <div style={s.barFill(Math.round((count / total) * 100), 'var(--slate)')} />
            </div>
            <div style={s.barCount}>{count}</div>
          </div>
        ))}
      </div>

      <div style={s.model}>
        Embeddings: {stats.embedding_model}<br />
        LLM: {stats.chat_model}
      </div>
    </div>
  )
}
