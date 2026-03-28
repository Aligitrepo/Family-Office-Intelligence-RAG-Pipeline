const BASE = '/api'

export async function fetchStats() {
  const res = await fetch(`${BASE}/stats`)
  if (!res.ok) throw new Error(`Stats error: ${res.status}`)
  return res.json()
}

export async function fetchExamples() {
  const res = await fetch(`${BASE}/examples`)
  if (!res.ok) throw new Error(`Examples error: ${res.status}`)
  return res.json()
}

export async function fetchHealth() {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) throw new Error(`Health error: ${res.status}`)
  return res.json()
}

/**
 * @param {string} query
 * @param {object} filters - { fo_type, hq_country, min_aum_usd_m, max_aum_usd_m, has_check_size, has_strategy, confidence_score }
 * @param {number} k - number of documents to retrieve
 */
export async function queryPipeline(query, filters = {}, k = 8) {
  const body = { query, k, ...filters }
  // Remove undefined/null/empty values
  Object.keys(body).forEach(key => {
    if (body[key] === undefined || body[key] === null || body[key] === '') {
      delete body[key]
    }
  })

  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `Query error: ${res.status}`)
  }
  return res.json()
}
