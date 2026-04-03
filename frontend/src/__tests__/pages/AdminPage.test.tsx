import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../utils/testUtils'
import { server } from '../../__mocks__/server'
import AdminPage from '../../pages/AdminPage'

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('AdminPage', () => {
  it('renders page title', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('管理ページ')).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    render(<AdminPage />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('renders notice management section', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('お知らせ管理')).toBeInTheDocument()
    })
  })

  it('renders question management section', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('定型質問管理')).toBeInTheDocument()
    })
  })

  it('renders add notice button', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('お知らせ追加')).toBeInTheDocument()
    })
  })

  it('renders add question button', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('質問追加')).toBeInTheDocument()
    })
  })

  it('opens notice dialog when add button clicked', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('お知らせ管理')).toBeInTheDocument()
    })
    
    const addButtons = screen.getAllByText('お知らせ追加')
    fireEvent.click(addButtons[0])
    
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })
})
