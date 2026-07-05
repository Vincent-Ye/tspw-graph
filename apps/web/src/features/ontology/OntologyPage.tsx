import { useEffect, useState } from 'react'

import { apiFetch, type OntologyCatalog } from '../../api/client'

export function OntologyPage() {
  const [catalog, setCatalog] = useState<OntologyCatalog>()
  const [error, setError] = useState('')
  const [view, setView] = useState<'tbox' | 'abox'>('tbox')
  useEffect(() => { apiFetch<OntologyCatalog>('/api/ontology').then(setCatalog).catch((e: Error) => setError(e.message)) }, [])
  return <section className="page">
    <header className="page-header"><div><p className="eyebrow">ONTOLOGY · 02</p><h1>先定义江湖，再描述江湖</h1><p>本体不是一张漂亮的关系图，而是一套对所有事实生效的概念与约束。</p></div><div className="segmented"><button className={view === 'tbox' ? 'active' : ''} onClick={() => setView('tbox')}>TBox 概念层</button><button className={view === 'abox' ? 'active' : ''} onClick={() => setView('abox')}>ABox 实例层</button></div></header>
    {error && <div role="alert" className="error-state">{error}</div>}
    {!catalog && !error && <div className="skeleton" aria-label="正在加载本体" />}
    {catalog && view === 'tbox' && <div className="ontology-grid">{catalog.entity_types.map(type => <article className="type-card" key={type.id} style={{ '--type-color': type.color } as React.CSSProperties}><span>{type.parent ? '子类' : '核心类'}</span><h2>{type.label}</h2><code>{type.id}</code><p>{type.description}</p>{type.parent && <small>继承自 {type.parent}</small>}</article>)}</div>}
    {catalog && view === 'abox' && <div className="abox"><div className="abox-node">令狐冲 <small>Person</small></div><div className="abox-edge">— 掌握 →</div><div className="abox-node accent">独孤九剑 <small>Swordplay</small></div><aside><b>满足本体约束</b><p>KNOWS 的主体必须是人物，客体必须是武学。</p><code>{JSON.stringify(catalog.example, null, 2)}</code></aside></div>}
  </section>
}

