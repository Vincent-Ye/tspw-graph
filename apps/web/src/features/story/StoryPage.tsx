import { useEffect, useState } from 'react'

import { apiFetch, PROJECT_ID, type EntitySummary } from '../../api/client'

type TimelineItem = { event: EntitySummary; chapter_number?: number }

export function StoryPage() {
  const [people, setPeople] = useState<EntitySummary[]>([])
  const [person, setPerson] = useState('')
  const [events, setEvents] = useState<TimelineItem[]>([])
  useEffect(() => { apiFetch<EntitySummary[]>(`/api/graph/search?project_id=${PROJECT_ID}&query=${encodeURIComponent('令狐')}&types=Person`).then(setPeople) }, [])
  useEffect(() => { const suffix = person ? `&person_id=${encodeURIComponent(person)}` : ''; apiFetch<TimelineItem[]>(`/api/graph/timeline?project_id=${PROJECT_ID}${suffix}`).then(setEvents) }, [person])
  return <section className="page narrow"><header className="page-header"><div><p className="eyebrow">STORY LINE · 04</p><h1>关系会随故事改变</h1><p>时间线把静态关系放回章节语境，区分“曾经属于”和“此刻属于”。</p></div><label className="select-label">人物<select aria-label="人物" value={person} onChange={event => setPerson(event.target.value)}><option value="">全部人物</option>{people.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></header><ol className="timeline">{events.map(item => <li key={item.event.id}><span>{item.chapter_number ? `第 ${item.chapter_number} 章` : '章节待考'}</span><article><p className="eyebrow">{item.event.type}</p><h2>{item.event.name}</h2><p>{item.event.description}</p></article></li>)}{events.length === 0 && <li className="empty-state">当前条件下没有事件</li>}</ol></section>
}

