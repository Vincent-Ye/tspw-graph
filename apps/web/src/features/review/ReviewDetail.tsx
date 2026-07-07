import type { ReviewActionRequest, ReviewItem } from '../../api/client'

export function ReviewDetail({
  item,
  onAction,
}: {
  item?: ReviewItem
  onAction: (request: ReviewActionRequest) => void
}) {
  if (!item) {
    return (
      <section className="review-detail">
        <h2>选择一个待审核项</h2>
      </section>
    )
  }

  const factId = item.target.fact_id ?? ''
  return (
    <section className="review-detail">
      <p className="eyebrow">{item.item_type}</p>
      <h2>审核详情</h2>
      <pre>{JSON.stringify(item.target, null, 2)}</pre>
      <div className="review-actions">
        {item.item_type === 'FACT' && (
          <>
            <button
              onClick={() =>
                onAction({
                  action_type: 'accept_fact',
                  payload: { fact_id: factId },
                  idempotency_key: `accept-${item.id}`,
                })
              }
            >
              接受事实
            </button>
            <button
              onClick={() =>
                onAction({
                  action_type: 'reject_fact',
                  payload: { fact_id: factId },
                  idempotency_key: `reject-${item.id}`,
                })
              }
            >
              拒绝事实
            </button>
          </>
        )}
        <button
          onClick={() =>
            onAction({
              action_type: 'dismiss_item',
              payload: {},
              idempotency_key: `dismiss-${item.id}`,
            })
          }
        >
          忽略
        </button>
      </div>
    </section>
  )
}
