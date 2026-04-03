import { describe, it, expect, vi, beforeEach } from 'vitest'
import { chatApi } from '../../services/chatApi'

vi.mock('../../services/api', () => ({
  api: {
    post: vi.fn()
  }
}))

describe('chatApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should send message', async () => {
    const mockApi = await import('../../services/api')
    const mockPost = mockApi.api.post as any
    mockPost.mockResolvedValue({
      response: 'AI response',
      agent_type: 'test_agent',
      session_id: 'session-123',
      actor_id: 'test_actor'
    })

    const result = await chatApi.sendMessage({
      agent_type: 'test_agent',
      prompt: 'Hello',
      session_id: 'session-123',
      survey_id: 'test_survey'
    })

    expect(mockPost).toHaveBeenCalledWith('/api/chat/message', expect.any(Object))
    expect(result.response).toBe('AI response')
  })

  it('should save session', async () => {
    const mockApi = await import('../../services/api')
    const mockPost = mockApi.api.post as any
    mockPost.mockResolvedValue({
      message: 'Session saved successfully'
    })

    const result = await chatApi.saveSession({
      survey_id: 'test_survey',
      session_id: 'session-123'
    })

    expect(mockPost).toHaveBeenCalledWith('/api/chat/session/save', expect.any(Object))
    expect(result.message).toBe('Session saved successfully')
  })
})
