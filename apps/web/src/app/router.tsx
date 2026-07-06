import { Navigate, Route, Routes } from 'react-router-dom'

import { AskPage } from '../features/ask/AskPage'
import { GraphPage } from '../features/graph/GraphPage'
import { GuidePage } from '../features/guide/GuidePage'
import { OntologyPage } from '../features/ontology/OntologyPage'
import { StoryPage } from '../features/story/StoryPage'
import { BuildPage } from '../features/build/BuildPage'

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
