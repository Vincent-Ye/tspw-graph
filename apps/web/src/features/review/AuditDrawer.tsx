import type { ReviewAction } from '../../api/client'

export function AuditDrawer({ actions }: { actions: ReviewAction[] }) {
  return (
    <aside className="audit-drawer">
      <h2>审计日志</h2>
      {actions.length === 0 ? (
        <p>暂无审核动作</p>
      ) : (
        actions.map((action) => (
          <article key={action.id}>
            <b>{action.action_type}</b>
            <span>{action.reviewer}</span>
          </article>
        ))
      )}
    </aside>
  )
}
