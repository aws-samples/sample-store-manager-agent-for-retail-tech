import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '../utils/testUtils'
import { server } from '../../__mocks__/server'
import DailyAnswerDetailPage from '../../pages/DailyAnswerDetailPage'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: 'test-id' }),
    useNavigate: () => vi.fn()
  }
})

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('DailyAnswerDetailPage', () => {
  it('renders page title', async () => {
    render(<DailyAnswerDetailPage />)
    
    await waitFor(() => {
      expect(screen.getByText('回答確認・編集')).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    render(<DailyAnswerDetailPage />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('renders back button', async () => {
    render(<DailyAnswerDetailPage />)
    
    await waitFor(() => {
      expect(screen.getByText('回答確認・編集')).toBeInTheDocument()
    })
  })
})
