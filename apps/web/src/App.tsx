import { BrowserRouter, NavLink } from 'react-router-dom'

import { AppRoutes } from './app/router'
import { ProjectProvider } from './app/ProjectContext'
import { ProjectSwitcher } from './features/projects/ProjectSwitcher'
import './styles/theme.css'

const links = [['/guide', '导览'], ['/ontology', '本体'], ['/graph', '图谱'], ['/story', '故事线'], ['/ask', '问答'], ['/build', '构建'], ['/review', '审核']]

export function App() {
  return <BrowserRouter><ProjectProvider><a className="skip-link" href="#main">跳到主要内容</a><header className="site-header"><NavLink className="brand" to="/guide"><span>江湖</span>图谱</NavLink><nav aria-label="主导航">{links.map(([path, label]) => <NavLink key={path} to={path}>{label}</NavLink>)}</nav><ProjectSwitcher /></header><main id="main"><AppRoutes /></main></ProjectProvider></BrowserRouter>
}
