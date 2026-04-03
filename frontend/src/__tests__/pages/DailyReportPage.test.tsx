import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '../utils/testUtils'
import { server } from '../../__mocks__/server'
import DailyReportPage from '../../pages/DailyReportPage'

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('DailyReportPage', () => {
  it('renders page title', async () => {
    render(<DailyReportPage />)
    
    await waitFor(() => {
      expect(screen.getByText('フィードバック')).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    render(<DailyReportPage />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('renders date selector', async () => {
    render(<DailyReportPage />)
    
    await waitFor(() => {
      expect(screen.getByText('内容')).toBeInTheDocument()
    })
  })
})
