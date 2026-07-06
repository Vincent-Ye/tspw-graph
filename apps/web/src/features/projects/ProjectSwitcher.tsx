import { useProject } from '../../app/ProjectContext'

export function ProjectSwitcher() {
  const { projects, projectId, setProjectId } = useProject()
  return <label className="project-switcher"><span>当前项目</span><select aria-label="当前项目" value={projectId} onChange={event => setProjectId(event.target.value)}><option value="xiaoao">笑傲江湖</option>{projects.filter(item => item.id !== 'xiaoao').map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
}
