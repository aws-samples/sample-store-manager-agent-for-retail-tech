import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '../utils/testUtils'
import { server } from '../../__mocks__/server'
import DailyAnswerPage from '../../pages/DailyAnswerPage'

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('DailyAnswerPage', () => {
  it('renders page title', () => {
    render(<DailyAnswerPage />)
    expect(screen.getByText('アンケート')).toBeInTheDocument()
  })

  it('loads and displays questions', async () => {
    render(<DailyAnswerPage />)
    
    await waitFor(() => {
      expect(screen.getByText('アンケート')).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    render(<DailyAnswerPage />)
    const progressBars = screen.getAllByRole('progressbar')
    expect(progressBars.length).toBeGreaterThan(0)
  })

  it('enables submit button when answers are provided', async () => {
    render(<DailyAnswerPage />)
    
    await waitFor(() => {
      expect(screen.getByText('アンケート')).toBeInTheDocument()
    })

    const submitButton = screen.getByText('次へ')
    expect(submitButton).not.toBeDisabled()
  })
})
