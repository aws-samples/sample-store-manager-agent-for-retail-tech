import { describe, it, expect, vi, beforeEach } from 'vitest'
import { surveyApi } from '../../services/surveyApi'

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn()
  }
}))

describe('surveyApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get answers', async () => {
    const mockApi = await import('../../services/api')
    const mockGet = mockApi.api.get as any
    mockGet.mockResolvedValue({
      answers: [{ survey_id: '1', user_cd: 'test_user' }],
      total_count: 1
    })

    const result = await surveyApi.getAnswers({
      page: 1,
      limit: 30
    })

    expect(mockGet).toHaveBeenCalledWith('/api/survey/answers', expect.any(Object))
    expect(result.answers).toHaveLength(1)
  })

  it('should create answer', async () => {
    const mockApi = await import('../../services/api')
    const mockPost = mockApi.api.post as any
    mockPost.mockResolvedValue({ survey_id: 'test-id', message: 'Success' })

    const result = await surveyApi.createAnswer({
      survey_id: 'test-survey',
      answers: [{
        question_id: 'q1',
        question_text: 'Test Question',
        question_type: 'text',
        answer_value: 'test'
      }]
    })

    expect(mockPost).toHaveBeenCalledWith('/api/survey/answers', expect.any(Object))
    expect(result.survey_id).toBe('test-id')
  })
})
