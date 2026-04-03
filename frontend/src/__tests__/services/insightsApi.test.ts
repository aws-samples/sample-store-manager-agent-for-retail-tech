import { describe, it, expect, vi, beforeEach } from 'vitest'
import { insightsApi } from '../../services/insightsApi'

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

describe('insightsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get daily insight', async () => {
    const mockApi = await import('../../services/api')
    const mockGet = mockApi.api.get as any
    mockGet.mockResolvedValue({
      id: 'insight-1',
      user_cd: 'test_user',
      str_cd: 'test_store',
      report_date: '2024-01-01',
      status: 'completed',
      report_text: 'Test insight'
    })

    const result = await insightsApi.getDailyInsight({
      report_date: '2024-01-01'
    })

    expect(mockGet).toHaveBeenCalledWith('/api/insights/daily', expect.any(Object))
    expect(result.id).toBe('insight-1')
  })

  it('should generate daily insight with summary_id and report_date', async () => {
    const mockApi = await import('../../services/api')
    const mockPost = mockApi.api.post as any
    mockPost.mockResolvedValue({
      response: 'Generated insight text',
      agent_type: 'daily_summary',
      session_id: 'session-123',
      actor_id: 'actor-456',
      summary_id: 'summary-789'
    })

    const result = await insightsApi.generateDailyInsight({
      agent_type: 'daily_summary',
      prompt: 'Generate insight',
      session_id: 'session-123',
      report_date: '2024-01-01'
    })

    expect(mockPost).toHaveBeenCalledWith('/api/insights/daily/generate', expect.objectContaining({
      report_date: '2024-01-01'
    }))
    expect(result.summary_id).toBe('summary-789')
  })

  it('should get daily insight history', async () => {
    const mockApi = await import('../../services/api')
    const mockGet = mockApi.api.get as any
    mockGet.mockResolvedValue({
      insights: [{ id: '1', report_date: '2024-01-01' }],
      total_count: 1,
      current_page: 1,
      total_pages: 1
    })

    const result = await insightsApi.getDailyInsightHistory({
      page: 1,
      limit: 30
    })

    expect(mockGet).toHaveBeenCalledWith('/api/insights/daily/history', expect.any(Object))
    expect(result.insights).toHaveLength(1)
  })
})
