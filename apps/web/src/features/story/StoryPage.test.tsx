import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { StoryPage } from './StoryPage'

describe('StoryPage', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('filters the story line by person', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const url = String(input)
      if (url.includes('/search')) return new Response(JSON.stringify([
        { id: 'linghu', project_id: 'xiaoao', type: 'Person', name: '令狐沖', aliases: ['令狐冲'], description: '' },
      ]))
      return new Response(JSON.stringify([
        { event: { id: 'teaching', project_id: 'xiaoao', type: 'TeachingEvent', name: '思過崖傳劍', aliases: ['思过崖传剑'], description: '风清扬指点令狐冲。' }, chapter_number: 10 },
      ]))
    }))
    const user = userEvent.setup()
    render(<StoryPage />)

    await user.selectOptions(await screen.findByRole('combobox', { name: '人物' }), 'linghu')

    expect(await screen.findByText('思過崖傳劍')).toBeVisible()
  })
})
