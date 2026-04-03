import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen } from '../utils/testUtils'
import { server } from '../../__mocks__/server'
import AnswerConfirmPage from '../../pages/AnswerConfirmPage'

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('AnswerConfirmPage', () => {
  it('renders page title', () => {
    render(<AnswerConfirmPage />)
    expect(screen.getByText('回答確認・編集')).toBeInTheDocument()
  })

  it('renders confirm button', () => {
    render(<AnswerConfirmPage />)
    expect(screen.getByText('完了')).toBeInTheDocument()
  })

  it('renders back button', () => {
    render(<AnswerConfirmPage />)
    expect(screen.queryByText('キャンセル')).not.toBeInTheDocument()
  })
})
