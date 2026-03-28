import React from 'react'
import { SlidersHorizontal } from 'lucide-react'

const s = {
  panel: {
    background: 'var(--card-bg)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '16px',
    backdropFilter: 'blur(8px)',
  },
  title: {
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: 'var(--gold)',
    marginBottom: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  group: { marginBottom: '12px' },
  label: {
    display: 'block',
    fontSize: '11px',
    color: 'var(--slate)',
    marginBottom: '5px',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
    fontWeight: 600,
  },
  select: {
    width: '100%',
    background: 'rgba(15,31,61,0.7)',
    border: '1px solid rgba(201,168,76,0.2)',
    borderRadius: '6px',
    color: 'var(--white)',
    padding: '7px 10px',
    fontSize: '12px',
    outline: 'none',
    cursor: 'pointer',
  },
  input: {
    width: '100%',
    background: 'rgba(15,31,61,0.7)',
    border: '1px solid rgba(201,168,76,0.2)',
    borderRadius: '6px',
    color: 'var(--white)',
    padding: '7px 10px',
    fontSize: '12px',
    outline: 'none',
  },
  row: { display: 'flex', gap: '8px' },
  kLabel: { fontSize: '11px', color: 'var(--slate)', marginBottom: '5px', display: 'flex', justifyContent: 'space-between' },
  kVal: { color: 'var(--gold-light)', fontWeight: 600 },
  slider: { width: '100%', accentColor: 'var(--gold)' },
  resetBtn: {
    width: '100%',
    padding: '8px',
    background: 'transparent',
    border: '1px solid rgba(201,168,76,0.3)',
    borderRadius: '6px',
    color: 'var(--slate)',
    fontSize: '12px',
    marginTop: '8px',
    transition: 'border-color 0.2s, color 0.2s',
  },
}

const COUNTRIES = [
  'United States','United Kingdom','France','Germany','Switzerland','Sweden',
  'Belgium','Netherlands','Canada','Australia','India','Japan','Hong Kong',
  'Singapore','Spain','Norway','Denmark','Liechtenstein','South Africa',
  'Brazil','Mexico','Israel','United Arab Emirates','Italy','Ireland',
]

export default function FilterPanel({ filters, setFilters }) {
  const set = (key, val) => setFilters(f => ({ ...f, [key]: val }))
  const reset = () => setFilters({
    fo_type: '', hq_country: '', min_aum_usd_m: '', max_aum_usd_m: '',
    has_check_size: '', has_strategy: '', confidence_score: '', k: 8,
  })

  return (
    <div style={s.panel}>
      <div style={s.title}><SlidersHorizontal size={13} /> Filters</div>

      <div style={s.group}>
        <label style={s.label}>FO Type</label>
        <select style={s.select} value={filters.fo_type || ''} onChange={e => set('fo_type', e.target.value)}>
          <option value="">All types</option>
          <option value="SFO">SFO — Single Family Office</option>
          <option value="MFO">MFO — Multi-Family Office</option>
        </select>
      </div>

      <div style={s.group}>
        <label style={s.label}>Country</label>
        <select style={s.select} value={filters.hq_country || ''} onChange={e => set('hq_country', e.target.value)}>
          <option value="">All countries</option>
          {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div style={s.group}>
        <label style={s.label}>AUM Range (USD M)</label>
        <div style={s.row}>
          <input style={s.input} type="number" placeholder="Min" value={filters.min_aum_usd_m || ''}
            onChange={e => set('min_aum_usd_m', e.target.value ? parseFloat(e.target.value) : '')} />
          <input style={s.input} type="number" placeholder="Max" value={filters.max_aum_usd_m || ''}
            onChange={e => set('max_aum_usd_m', e.target.value ? parseFloat(e.target.value) : '')} />
        </div>
      </div>

      <div style={s.group}>
        <label style={s.label}>Confidence</label>
        <select style={s.select} value={filters.confidence_score || ''} onChange={e => set('confidence_score', e.target.value)}>
          <option value="">All</option>
          <option value="H">High confidence only</option>
          <option value="M">Medium confidence only</option>
        </select>
      </div>

      <div style={s.group}>
        <label style={s.label}>Data Completeness</label>
        <select style={s.select} value={filters.has_strategy || ''} onChange={e => set('has_strategy', e.target.value === '' ? '' : e.target.value === 'true')}>
          <option value="">Any record</option>
          <option value="true">Has investment strategy</option>
        </select>
      </div>

      <div style={s.group}>
        <label style={s.label}>Check Size Data</label>
        <select style={s.select} value={filters.has_check_size || ''} onChange={e => set('has_check_size', e.target.value === '' ? '' : e.target.value === 'true')}>
          <option value="">Any record</option>
          <option value="true">Has check size data</option>
        </select>
      </div>

      <div style={s.group}>
        <div style={s.kLabel}>
          <span>Results to retrieve</span>
          <span style={s.kVal}>{filters.k || 8}</span>
        </div>
        <input style={s.slider} type="range" min={3} max={20} value={filters.k || 8}
          onChange={e => set('k', parseInt(e.target.value))} />
      </div>

      <button style={s.resetBtn} onClick={reset}>Reset all filters</button>
    </div>
  )
}
