import { useCallback, useEffect, useState } from 'react'

import { apiFetch, PROJECT_ID, type EntityDetail, type EntitySummary, type Neighborhood } from '../../api/client'
import { EntityPanel } from './EntityPanel'
import { GraphCanvas } from './GraphCanvas'

const EMPTY_GRAPH: Neighborhood = { nodes: [], edges: [] }

export function GraphPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<EntitySummary[]>([])
  const [graph, setGraph] = useState<Neighborhood>(EMPTY_GRAPH)
  const [detail, setDetail] = useState<EntityDetail>()
  const [error, setError] = useState('')
  useEffect(() => {
    if (!query.trim()) { setResults([]); setError(''); return }
    const timer = window.setTimeout(() => {
      apiFetch<EntitySummary[]>(`/api/graph/search?project_id=${PROJECT_ID}&query=${encodeURIComponent(query)}`)
        .then(nextResults => { setResults(nextResults); setError('') })
        .catch((e: Error) => setError(e.message))
    }, 180)
    return () => window.clearTimeout(timer)
  }, [query])
  const selectEntity = useCallback((id: string) => {
    setResults([]); setError('')
    Promise.all([
      apiFetch<EntityDetail>(`/api/entities/${encodeURIComponent(id)}?project_id=${PROJECT_ID}`),
      apiFetch<Neighborhood>(`/api/graph/neighborhood?project_id=${PROJECT_ID}&entity_id=${encodeURIComponent(id)}&depth=2`),
    ]).then(([nextDetail, nextGraph]) => { setDetail(nextDetail); setGraph(nextGraph) }).catch((e: Error) => setError(e.message))
  }, [])
  return <section className="graph-page"><header className="graph-toolbar"><div><p className="eyebrow">GRAPH EXPLORER · 03</p><h1>沿关系，游江湖</h1></div><div className="search-wrap"><label htmlFor="graph-search">搜索人物、门派或武学</label><input id="graph-search" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="例如：令狐冲" />{results.length > 0 && <div className="search-results">{results.map(item => <button key={item.id} onClick={() => selectEntity(item.id)}><b>{item.name}</b><span>{item.type} · {item.description}</span></button>)}</div>}</div></header>{error && <div role="alert" className="error-state">{error}</div>}<div className="graph-workspace"><GraphCanvas graph={graph} onSelect={selectEntity} /><EntityPanel detail={detail} onClose={() => setDetail(undefined)} /></div><footer className="graph-legend"><span><i className="person-dot" />人物</span><span><i />其他实体</span><b>{graph.nodes.length} 节点 · {graph.edges.length} 关系</b></footer></section>
}
