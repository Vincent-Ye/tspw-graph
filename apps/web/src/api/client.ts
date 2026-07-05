export const PROJECT_ID = 'xiaoao'

export type EntitySummary = {
  id: string
  project_id: string
  type: string
  name: string
  aliases: string[]
  description: string
}

export type Evidence = {
  id: string
  chapter_id: string
  chapter_number: number
  chapter_title: string
  start_offset: number
  end_offset: number
  quote: string
}

export type Fact = {
  id: string
  type: string
  source_id: string
  target_id: string
  evidence: Evidence[]
}

export type EntityDetail = EntitySummary & { facts: Fact[] }

export type GraphEdge = {
  id: string
  source_id: string
  target_id: string
  type: string
  from_chapter?: number
  to_chapter?: number
  confidence: number
}

export type Neighborhood = { nodes: EntitySummary[]; edges: GraphEdge[] }

export type OntologyCatalog = {
  entity_types: Array<{ id: string; label: string; description: string; color: string; parent?: string }>
  relation_types: Array<{ id: string; label: string; description: string; source_types: string[]; target_types: string[]; symmetric: boolean; temporal: boolean }>
  example: { subject: string; predicate: string; object: string }
}

export type AskResponse = {
  answer: string
  path: Array<{ source_name: string; relation: string; target_name: string }>
  query_explanation: string
  cypher_template: string
  parameters: Record<string, string>
  evidence: Evidence[]
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) throw new Error(`请求失败（${response.status}）`)
  return response.json() as Promise<T>
}

