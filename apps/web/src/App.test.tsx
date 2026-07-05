import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  it('shows the product brand and page heading', () => {
    render(<App />)
    expect(screen.getByRole('link', { name: /江湖.*图谱/ })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /看懂《笑傲江湖》.*也看懂知识图谱/ })).toBeInTheDocument()
  })
})
