import { describe, it, expect, vi } from 'vitest'

vi.mock('../../services/apiClient', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('api service', () => {
  it('should make GET request', async () => {
    const { api } = await import('../../services/api')
    const mockApiClient = await import('../../services/apiClient')
    const mockGet = mockApiClient.default.get as any
    mockGet.mockResolvedValue({ data: { test: 'data' } })

    const result = await api.get('/test')
    expect(result).toEqual({ test: 'data' })
    expect(mockGet).toHaveBeenCalledWith('/test', { params: undefined })
  })

  it('should make POST request', async () => {
    const { api } = await import('../../services/api')
    const mockApiClient = await import('../../services/apiClient')
    const mockPost = mockApiClient.default.post as any
    mockPost.mockResolvedValue({ data: { success: true } })

    const result = await api.post('/test', { data: 'test' })
    expect(result).toEqual({ success: true })
    expect(mockPost).toHaveBeenCalledWith('/test', { data: 'test' })
  })
})
