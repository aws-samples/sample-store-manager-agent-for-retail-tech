import React from 'react'
import { render, type RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { vi } from 'vitest'

const theme = createTheme()

vi.mock('../../stores/appStore', () => ({
  useAppStore: vi.fn((selector) => {
    const state = {
      user: { name: 'Test User', store: 'admin', email: 'test@example.com', userId: 'test-user-id' },
      sidebarCollapsed: false,
      currentAnswers: [],
      chatHistory: [],
      reports: [],
      loading: false,
      supplementComment: '',
      isInitialized: true,
      chatSession: null,
      notification: { open: false, message: '', severity: 'success' as const },
      setSidebarCollapsed: vi.fn(),
      addAnswer: vi.fn(),
      updateAnswer: vi.fn(),
      addChatMessage: vi.fn(),
      setLoading: vi.fn(),
      saveReport: vi.fn(),
      loadStoredData: vi.fn(),
      clearAnswers: vi.fn(),
      clearChatHistory: vi.fn(),
      showNotification: vi.fn(),
      hideNotification: vi.fn(),
      setChatSession: vi.fn(),
      getChatSession: vi.fn(),
      setUser: vi.fn(),
      reset: vi.fn(),
    }
    return selector ? selector(state) : state
  }),
}))

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </BrowserRouter>
  )
}

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
