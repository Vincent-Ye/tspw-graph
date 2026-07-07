import type { ReviewSummary as Summary } from '../../api/client'

export function ReviewSummary({ summary }: { summary: Summary }) {
  const metrics = [
    ['待审核项', summary.open_review_items],
    ['已接受事实', summary.accepted_facts],
    ['已拒绝事实', summary.rejected_facts],
    ['合并实体', summary.merged_entities],
    ['拆出别名', summary.split_aliases],
    ['证据覆盖率', `${Math.round(summary.evidence_coverage * 100)}%`],
  ]
  return (
    <section className="quality-report">
      <p className="eyebrow">REVIEW QUALITY</p>
      <h2>质量仪表盘</h2>
      <div className="quality-metrics">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
