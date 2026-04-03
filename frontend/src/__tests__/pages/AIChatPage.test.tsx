import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '../utils/testUtils'
import { server } from '../../__mocks__/server'
import AIChatPage from '../../pages/AIChatPage'

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('AIChatPage', () => {
  it('renders page title', () => {
    render(<AIChatPage />)
    expect(screen.getByText('AIチャット')).toBeInTheDocument()
  })

  it('renders message input', () => {
    render(<AIChatPage />)
    expect(screen.getByPlaceholderText('メッセージを入力してください...')).toBeInTheDocument()
  })

  it('renders send button', () => {
    render(<AIChatPage />)
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('disables send button when input is empty', () => {
    render(<AIChatPage />)
    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeDisabled()
  })

  it('enables send button when input has text', () => {
    render(<AIChatPage />)
    const input = screen.getByPlaceholderText('メッセージを入力してください...')
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(input, { target: { value: 'Hello' } })
    expect(sendButton).not.toBeDisabled()
  })
})
