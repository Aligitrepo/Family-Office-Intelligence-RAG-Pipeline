import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Search, Zap, ChevronRight, AlertCircle, Loader2, BookOpen } from 'lucide-react'
import StatsPanel from './components/StatsPanel.jsx'
import FilterPanel from './components/FilterPanel.jsx'
import ResultCard from './components/ResultCard.jsx'
import { fetchStats, fetchExamples, queryPipeline } from './api.js'

/* ── Styles ──────────────────────────────────────────────────────────────── */
const s = {
  layout: {
    display: 'grid',
    gridTemplateColumns: '280px 1fr 300px',
    gridTemplateRows: 'auto 1fr',
    gap: '0',
    minHeight: '100vh',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    gridColumn: '1 / -1',
    padding: '18px 28px',
    borderBottom: '1px solid var(--border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: 'rgba(15,31,61,0.9)',
    backdropFilter: 'blur(8px)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logoIcon: {
    width: '32px',
    height: '32px',
    background: 'linear-gradient(135deg, var(--gold), var(--navy-light))',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: '16px',
    fontWeight: 700,
    color: 'var(--white)',
    letterSpacing: '-0.01em',
  },
  logoSub: {
    fontSize: '11px',
    color: 'var(--slate)',
    marginTop: '1px',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    fontSize: '12px',
    color: 'var(--slate)',
  },
  statusDot: (ok) => ({
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    background: ok ? '#6ab187' : '#e07070',
    display: 'inline-block',
    marginRight: '5px',
  }),

  // Columns
  leftCol: {
    padding: '20px 16px',
    borderRight: '1px solid var(--border)',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  centerCol: {
    display: 'flex',
    flexDirection: 'column',
    overflowY: 'auto',
  },
  rightCol: {
    padding: '20px 16px',
    borderLeft: '1px solid var(--border)',
    overflowY: 'auto',
  },

  // Query area
  queryArea: {
    padding: '20px 24px',
    borderBottom: '1px solid var(--border)',
    background: 'rgba(15,31,61,0.5)',
  },
  queryRow: {
    display: 'flex',
    gap: '10px',
    alignItems: 'flex-end',
  },
  textarea: {
    flex: 1,
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(201,168,76,0.3)',
    borderRadius: '8px',
    color: 'var(--white)',
    padding: '12px 14px',
    fontSize: '14px',
    outline: 'none',
    resize: 'vertical',
    minHeight: '54px',
    maxHeight: '200px',
    lineHeight: 1.5,
    transition: 'border-color 0.2s',
  },
  submitBtn: {
    padding: '12px 20px',
    background: 'linear-gradient(135deg, var(--gold), #a8863a)',
    border: 'none',
    borderRadius: '8px',
    color: '#0f1f3d',
    fontWeight: 700,
    fontSize: '13px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    flexShrink: 0,
    transition: 'opacity 0.2s',
    height: '54px',
  },
  submitBtnDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },

  // Examples
  examplesRow: {
    marginTop: '12px',
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  exampleChip: {
    padding: '5px 12px',
    background: 'rgba(201,168,76,0.1)',
    border: '1px solid rgba(201,168,76,0.2)',
    borderRadius: '20px',
    fontSize: '11px',
    color: 'var(--gold-light)',
    cursor: 'pointer',
    transition: 'background 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
  },

  // Results
  resultsArea: {
    flex: 1,
    padding: '20px 24px',
    overflowY: 'auto',
  },
  answerBox: {
    background: 'var(--card-bg)',
    border: '1px solid rgba(201,168,76,0.3)',
    borderRadius: 'var(--radius)',
    padding: '20px',
    marginBottom: '20px',
    backdropFilter: 'blur(8px)',
    borderLeft: '3px solid var(--gold)',
  },
  answerHeader: {
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: 'var(--gold)',
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '7px',
  },
  answerText: {
    fontSize: '14px',
    lineHeight: 1.8,
    color: 'var(--slate-light)',
  },
  metaRow: {
    marginTop: '12px',
    fontSize: '11px',
    color: 'var(--slate)',
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap',
    fontFamily: 'var(--mono)',
  },
  recordsHeader: {
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: 'var(--slate)',
    marginBottom: '10px',
    display: 'flex',
    alignItems: 'center',
    gap: '7px',
  },
  recordsList: { display: 'flex', flexDirection: 'column', gap: '6px' },

  // Error / loading
  errorBox: {
    background: 'rgba(224,112,112,0.1)',
    border: '1px solid rgba(224,112,112,0.3)',
    borderRadius: '8px',
    padding: '14px 16px',
    fontSize: '13px',
    color: '#e07070',
    display: 'flex',
    gap: '10px',
    alignItems: 'flex-start',
  },
  loadingBox: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    color: 'var(--slate)',
    fontSize: '13px',
    padding: '20px 0',
  },
  empty: {
    padding: '60px 0',
    textAlign: 'center',
    color: 'var(--slate)',
  },
  emptyIcon: {
    fontSize: '40px',
    marginBottom: '12px',
    opacity: 0.3,
  },
  emptyText: { fontSize: '14px', marginBottom: '6px' },
  emptyHint: { fontSize: '12px', opacity: 0.6 },
}

/* ── App ────────────────────────────────────────────────────────────────── */
export default function App() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({ k: 8 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)
  const [examples, setExamples] = useState([])
  const [pipelineOk, setPipelineOk] = useState(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    fetchStats()
      .then(s => { setStats(s); setStatsLoading(false); setPipelineOk(true) })
      .catch(() => { setStatsLoading(false); setPipelineOk(false) })
    fetchExamples()
      .then(d => setExamples(d.examples || []))
      .catch(() => {})
  }, [])

  const submit = async () => {
    if (!query.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const cleanFilters = {}
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== '' && v !== null && v !== undefined && k !== 'k') cleanFilters[k] = v
      })
      const data = await queryPipeline(query.trim(), cleanFilters, filters.k || 8)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
  }

  const useExample = (q, exampleFilters = {}) => {
    setQuery(q)
    setFilters(f => ({
      k: f.k || 8,
      fo_type: '',
      hq_country: '',
      min_aum_usd_m: '',
      max_aum_usd_m: '',
      has_check_size: '',
      has_strategy: '',
      confidence_score: '',
      ...exampleFilters,
    }))
    textareaRef.current?.focus()
  }

  return (
    <div style={s.layout}>
      {/* Header */}
      <header style={s.header}>
        <div style={s.logo}>
          <div style={s.logoIcon}>
            <Zap size={16} color="#0f1f3d" />
          </div>
          <div>
            <div style={s.logoText}>Family Office Intelligence</div>
            <div style={s.logoSub}>PolarityIQ · RAG Pipeline · Task 2</div>
          </div>
        </div>
        <div style={s.headerRight}>
          <span>
            <span style={s.statusDot(pipelineOk)} />
            {pipelineOk === null ? 'Connecting…' : pipelineOk ? 'Pipeline ready' : 'Pipeline offline'}
          </span>
          {stats && <span>{stats.total_records} records · {Object.keys(stats.top_countries || {}).length} countries</span>}
        </div>
      </header>

      {/* Left column — filters */}
      <aside style={s.leftCol}>
        <FilterPanel filters={filters} setFilters={setFilters} />
      </aside>

      {/* Center column — query + results */}
      <main style={s.centerCol}>
        {/* Query input */}
        <div style={s.queryArea}>
          <div style={s.queryRow}>
            <textarea
              ref={textareaRef}
              style={s.textarea}
              placeholder="Ask anything about family offices — e.g. 'Which SFOs in Europe focus on tech?' or 'Who runs the largest Swiss MFOs?'"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKey}
              rows={2}
            />
            <button
              style={{ ...s.submitBtn, ...(loading || !query.trim() ? s.submitBtnDisabled : {}) }}
              onClick={submit}
              disabled={loading || !query.trim()}
            >
              {loading
                ? <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />
                : <Search size={15} />
              }
              {loading ? 'Searching…' : 'Query'}
            </button>
          </div>

          {/* Example chips */}
          {examples.length > 0 && (
            <div style={s.examplesRow}>
              {examples.slice(0, 4).map(ex => (
                <button key={ex.id} style={s.exampleChip} onClick={() => useExample(ex.query, ex.filters || {})}>
                  <ChevronRight size={10} />
                  {ex.category}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Results */}
        <div style={s.resultsArea}>
          {loading && (
            <div style={s.loadingBox}>
              <Loader2 size={16} style={{ animation: 'spin 1s linear infinite', color: 'var(--gold)' }} />
              Retrieving and generating answer…
            </div>
          )}

          {error && (
            <div style={s.errorBox}>
              <AlertCircle size={15} style={{ flexShrink: 0, marginTop: '1px' }} />
              <div><strong>Error:</strong> {error}</div>
            </div>
          )}

          {result && !loading && (
            <>
              {/* Answer */}
              <div style={s.answerBox}>
                <div style={s.answerHeader}><BookOpen size={12} /> Intelligence Answer</div>
                <div style={s.answerText}>
                  <ReactMarkdown>{result.answer}</ReactMarkdown>
                </div>
                <div style={s.metaRow}>
                  <span>model: {result.model_used}</span>
                  <span>retrieved: {result.retrieval_count} records</span>
                  {Object.keys(result.filters_applied).length > 0 && (
                    <span>filters: {JSON.stringify(result.filters_applied)}</span>
                  )}
                </div>
              </div>

              {/* Source records */}
              {result.records.length > 0 && (
                <>
                  <div style={s.recordsHeader}>
                    Source Records ({result.records.length})
                  </div>
                  <div style={s.recordsList}>
                    {result.records.map((rec, i) => (
                      <ResultCard key={rec.fo_id} record={rec} rank={i + 1} />
                    ))}
                  </div>
                </>
              )}
            </>
          )}

          {!result && !loading && !error && (
            <div style={s.empty}>
              <div style={s.emptyIcon}>🔍</div>
              <div style={s.emptyText}>Ask a question about family offices</div>
              <div style={s.emptyHint}>
                Use the filter panel to narrow results, or click an example above.
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Right column — stats */}
      <aside style={s.rightCol}>
        <StatsPanel stats={stats} loading={statsLoading} />
      </aside>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        textarea:focus { border-color: rgba(201,168,76,0.6) !important; box-shadow: 0 0 0 3px rgba(201,168,76,0.1); }
        button:hover:not(:disabled) { opacity: 0.88; }
      `}</style>
    </div>
  )
}
