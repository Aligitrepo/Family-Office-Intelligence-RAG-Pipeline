import React, { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, Building2, Globe, TrendingUp } from 'lucide-react'

const s = {
  card: (expanded) => ({
    background: expanded ? 'rgba(30,48,84,0.9)' : 'rgba(22,36,64,0.7)',
    border: '1px solid',
    borderColor: expanded ? 'rgba(201,168,76,0.4)' : 'rgba(201,168,76,0.15)',
    borderRadius: '8px',
    overflow: 'hidden',
    transition: 'border-color 0.2s',
  }),
  header: {
    padding: '12px 14px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    cursor: 'pointer',
    userSelect: 'none',
  },
  foId: {
    fontSize: '10px',
    fontFamily: 'var(--mono)',
    color: 'var(--gold)',
    background: 'rgba(201,168,76,0.12)',
    padding: '2px 7px',
    borderRadius: '4px',
    flexShrink: 0,
    fontWeight: 600,
  },
  name: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--white)',
    flex: 1,
  },
  typeBadge: (type) => ({
    fontSize: '10px',
    fontWeight: 700,
    padding: '2px 7px',
    borderRadius: '4px',
    flexShrink: 0,
    color: type === 'SFO' ? '#c9a84c' : type === 'MFO' ? '#5b9bd5' : '#8fa3c0',
    background: type === 'SFO' ? 'rgba(201,168,76,0.12)'
              : type === 'MFO' ? 'rgba(91,155,213,0.12)'
              : 'rgba(143,163,192,0.12)',
  }),
  confBadge: (conf) => ({
    fontSize: '10px',
    fontWeight: 700,
    padding: '2px 7px',
    borderRadius: '4px',
    color: conf === 'H' ? '#6ab187' : '#e8c97a',
    background: conf === 'H' ? 'rgba(106,177,135,0.12)' : 'rgba(232,201,122,0.12)',
  }),
  chevron: { color: 'var(--slate)', flexShrink: 0 },
  body: {
    padding: '0 14px 14px',
    borderTop: '1px solid rgba(201,168,76,0.1)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '8px',
    marginTop: '12px',
  },
  field: {
    fontSize: '12px',
  },
  fieldLabel: {
    fontSize: '10px',
    color: 'var(--slate)',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
    marginBottom: '2px',
  },
  fieldValue: {
    color: 'var(--slate-light)',
    fontWeight: 500,
  },
  distance: {
    marginTop: '10px',
    fontSize: '10px',
    color: 'var(--slate)',
    fontFamily: 'var(--mono)',
  },
  docText: {
    marginTop: '10px',
    fontSize: '11px',
    color: 'var(--slate)',
    lineHeight: 1.7,
    fontFamily: 'var(--mono)',
    background: 'rgba(15,31,61,0.4)',
    borderRadius: '6px',
    padding: '10px',
    maxHeight: '140px',
    overflowY: 'auto',
  },
}

function formatAUM(val) {
  if (!val || val < 0) return 'N/A'
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}T`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}B`
  return `$${val.toFixed(0)}M`
}

export default function ResultCard({ record, rank }) {
  const [expanded, setExpanded] = useState(false)
  const m = record.metadata || {}

  return (
    <div style={s.card(expanded)}>
      <div style={s.header} onClick={() => setExpanded(e => !e)}>
        <span style={{ fontSize: '11px', color: 'var(--slate)', width: '18px', flexShrink: 0 }}>{rank}</span>
        <span style={s.foId}>{record.fo_id}</span>
        <span style={s.name}>{record.fo_name}</span>
        <span style={s.typeBadge(record.fo_type)}>{record.fo_type}</span>
        <span style={s.confBadge(record.confidence_score)}>{record.confidence_score === 'H' ? 'High' : 'Med'}</span>
        {expanded ? <ChevronUp size={14} style={s.chevron} /> : <ChevronDown size={14} style={s.chevron} />}
      </div>

      {expanded && (
        <div style={s.body}>
          <div style={s.grid}>
            <div style={s.field}>
              <div style={s.fieldLabel}><Globe size={9} style={{ display:'inline', marginRight:3 }} />Location</div>
              <div style={s.fieldValue}>{[record.hq_city, record.hq_country].filter(Boolean).join(', ') || 'N/A'}</div>
            </div>
            <div style={s.field}>
              <div style={s.fieldLabel}><TrendingUp size={9} style={{ display:'inline', marginRight:3 }} />AUM</div>
              <div style={s.fieldValue}>{formatAUM(record.aum_usd_m)}</div>
            </div>
            {m.investment_strategy && (
              <div style={s.field}>
                <div style={s.fieldLabel}>Strategy</div>
                <div style={s.fieldValue}>{m.investment_strategy}</div>
              </div>
            )}
            {m.sector_focus && (
              <div style={s.field}>
                <div style={s.fieldLabel}>Sector Focus</div>
                <div style={s.fieldValue}>{m.sector_focus}</div>
              </div>
            )}
            {m.founding_family && (
              <div style={s.field}>
                <div style={s.fieldLabel}>Founding Family</div>
                <div style={s.fieldValue}>{m.founding_family}</div>
              </div>
            )}
            {m.registration_status && (
              <div style={s.field}>
                <div style={s.fieldLabel}>Registration</div>
                <div style={s.fieldValue}>{m.registration_status}</div>
              </div>
            )}
          </div>

          {m.website && m.website !== 'N/A' && (
            <div style={{ marginTop: '10px' }}>
              <a href={m.website} target="_blank" rel="noopener noreferrer"
                style={{ fontSize: '11px', color: 'var(--gold)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <ExternalLink size={10} /> {m.website}
              </a>
            </div>
          )}

          <div style={s.docText}>{record.document}</div>
          <div style={s.distance}>Semantic distance: {record.distance}</div>
        </div>
      )}
    </div>
  )
}
