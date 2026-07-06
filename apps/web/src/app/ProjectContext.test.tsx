import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import { ProjectProvider, useProject } from './ProjectContext'

function Probe() { const { projectId } = useProject(); return <span>{projectId}</span> }

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

it('restores the selected project from the URL', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify([]))))
  render(<MemoryRouter initialEntries={['/graph?project=project-1']}><ProjectProvider><Probe /></ProjectProvider></MemoryRouter>)
  expect(await screen.findByText('project-1')).toBeVisible()
})
