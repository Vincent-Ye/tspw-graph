import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ProjectProvider } from '../../app/ProjectContext'
import { ReviewPage } from './ReviewPage'

const fetchMock = vi.fn()

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

function json(data: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) } as Response)
}

function renderPage() {
  return render(
    <MemoryRouter>
      <QueryClientProvider client={new QueryClient()}>
        <ProjectProvider>
          <ReviewPage />
        </ProjectProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('ReviewPage', () => {
  it('shows quality summary, queue and applies a fact decision', async () => {
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/summary')) {
        return json({
          open_review_items: 1,
          accepted_facts: 2,
          rejected_facts: 0,
          pending_facts: 1,
          merged_entities: 0,
          split_aliases: 0,
          evidence_coverage: 0.8,
          review_completion_rate: 0.5,
          graph_fact_delta_before_after_review: 0,
        })
      }
      if (url.includes('/items/') && url.includes('/actions')) {
        return json({ item: { id: 'review-1', status: 'RESOLVED' }, action: { id: 'action-1' } })
      }
      if (url.includes('/items')) {
        return json({
          items: [
            {
              id: 'review-1',
              item_type: 'FACT',
              status: 'OPEN',
              reason_code: 'LOW_CONFIDENCE_FACT',
              target: { fact_id: 'fact-1' },
              evidence_ids: ['ev-1'],
              severity: 40,
              source: 'rule',
            },
          ],
        })
      }
      if (url.includes('/audit')) return json({ actions: [] })
      return json({})
    })
    renderPage()

    expect(await screen.findByText('审核工作台')).toBeInTheDocument()
    expect(screen.getByText('待审核项')).toBeInTheDocument()
    expect(screen.getByText('LOW_CONFIDENCE_FACT')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '接受事实' }))

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/review/items/review-1/actions'),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })
})
