import type { ReviewItem } from '../../api/client'

export function ReviewQueue({
  items,
  selectedId,
  onSelect,
}: {
  items: ReviewItem[]
  selectedId?: string
  onSelect: (item: ReviewItem) => void
}) {
  return (
    <aside className="review-queue">
      <h2>审核队列</h2>
      {items.map((item) => (
        <button
          className={item.id === selectedId ? 'active' : ''}
          key={item.id}
          onClick={() => onSelect(item)}
        >
          <b>{item.reason_code}</b>
          <span>
            {item.item_type} · {item.source} · severity {item.severity}
          </span>
        </button>
      ))}
    </aside>
  )
}
