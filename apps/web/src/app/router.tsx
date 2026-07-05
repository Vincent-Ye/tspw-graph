import { Navigate, Route, Routes } from 'react-router-dom'

import { AskPage } from '../features/ask/AskPage'
import { GraphPage } from '../features/graph/GraphPage'
import { GuidePage } from '../features/guide/GuidePage'
import { OntologyPage } from '../features/ontology/OntologyPage'
import { StoryPage } from '../features/story/StoryPage'

function BuildPage() {
  return <section className="page narrow"><p className="eyebrow">PHASE 2</p><h1>构建你的小说图谱</h1><div className="notice"><strong>在线构建将在 Phase 2 开放</strong><p>届时可上传 TXT，选择 OpenAI 兼容 API 或 Ollama，并观察分章抽取、消歧、校验和入图全过程。</p></div></section>
}

export function AppRoutes() {
  return <Routes>
    <Route path="/guide" element={<GuidePage />} />
    <Route path="/ontology" element={<OntologyPage />} />
    <Route path="/graph" element={<GraphPage />} />
    <Route path="/story" element={<StoryPage />} />
    <Route path="/ask" element={<AskPage />} />
    <Route path="/build" element={<BuildPage />} />
    <Route path="*" element={<Navigate to="/guide" replace />} />
  </Routes>
}

