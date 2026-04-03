import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '../utils/testUtils'
import { server } from '../../__mocks__/server'
import HistoryPage from '../../pages/HistoryPage'

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('HistoryPage', () => {
  it('renders page title', () => {
    render(<HistoryPage />)
    expect(screen.getByText('履歴')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    render(<HistoryPage />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('renders empty state when no data', async () => {
    render(<HistoryPage />)
    
    await waitFor(() => {
      expect(screen.getByText('作成日時')).toBeInTheDocument()
    })
  })

  it('renders pagination controls', () => {
    render(<HistoryPage />)
    expect(screen.getByRole('button', { name: /previous page/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument()
  })
})
