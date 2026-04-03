import { describe, it, expect, vi, beforeEach } from 'vitest'
import { adminApi } from '../../services/adminApi'

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('adminApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get messages', async () => {
    const mockApi = await import('../../services/api')
    const mockGet = mockApi.api.get as any
    mockGet.mockResolvedValue({
      messages: [{ admin_messages_id: '1', title: 'Test' }]
    })

    const result = await adminApi.getMessages({ is_active: true, limit: 10 })
    expect(mockGet).toHaveBeenCalledWith('/api/admin/messages', { is_active: true, limit: 10 })
    expect(result.messages).toHaveLength(1)
  })

  it('should create message', async () => {
    const mockApi = await import('../../services/api')
    const mockPost = mockApi.api.post as any
    mockPost.mockResolvedValue({
      admin_messages_id: 'new-id',
      message: 'Created'
    })

    const result = await adminApi.createMessage({
      title: 'New Message',
      content: 'Content',
      is_active: true
    })

    expect(mockPost).toHaveBeenCalledWith('/api/admin/messages', expect.any(Object))
    expect(result.admin_messages_id).toBe('new-id')
  })

  it('should get questions', async () => {
    const mockApi = await import('../../services/api')
    const mockGet = mockApi.api.get as any
    mockGet.mockResolvedValue({
      questions: [{ admin_survey_id: '1', question_text: 'Test' }]
    })

    const result = await adminApi.getQuestions({ is_active: true, limit: 10 })
    expect(mockGet).toHaveBeenCalledWith('/api/admin/survey/questions', { is_active: true, limit: 10 })
    expect(result.questions).toHaveLength(1)
  })
})
