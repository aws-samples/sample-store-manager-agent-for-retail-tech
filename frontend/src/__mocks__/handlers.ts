import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('http://localhost:8000/api/admin/messages', () => {
    return HttpResponse.json({
      messages: [
        {
          admin_messages_id: '1',
          title: 'Test Notice',
          content: 'Test content',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        }
      ]
    })
  }),

  http.get('http://localhost:8000/api/admin/survey/questions', () => {
    return HttpResponse.json({
      questions: [
        {
          admin_survey_id: '1',
          question_text: 'Test question',
          question_type: 'text',
          options: [],
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        }
      ]
    })
  }),

  http.get('http://localhost:8000/api/survey/questions', () => {
    return HttpResponse.json({
      questions: [
        {
          admin_survey_id: '1',
          question_text: 'Daily question',
          question_type: 'rating',
          options: [],
          is_active: true
        }
      ]
    })
  }),

  http.post('http://localhost:8000/api/survey/answers', () => {
    return HttpResponse.json({
      survey_id: 'test-survey-id',
      message: 'Success'
    })
  }),

  http.get('http://localhost:8000/api/insights/daily', () => {
    return HttpResponse.json({
      insights: [
        {
          date: '2024-01-01',
          content: 'Test daily insight'
        }
      ]
    })
  }),

  http.get('http://localhost:8000/api/insights/history', () => {
    return HttpResponse.json({
      surveys: [],
      total_count: 0
    })
  }),

  http.post('http://localhost:8000/api/chat/message', () => {
    return HttpResponse.json({
      response: 'AI response',
      session_id: 'test-session'
    })
  }),

  http.get('http://localhost:8000/api/survey/answers', () => {
    return HttpResponse.json({
      surveys: [],
      total_count: 0
    })
  }),

  http.post('http://localhost:8000/api/chat/session', () => {
    return HttpResponse.json({
      session_id: 'new-session-123'
    })
  }),

  http.get('http://localhost:8000/api/survey/answers/:surveyId', () => {
    return HttpResponse.json({
      survey_id: 'test-survey-id',
      user_cd: 'test_user_001',
      str_cd: 'test_store_001',
      answers: [
        {
          question_id: '1',
          question_text: 'Test question',
          question_type: 'text',
          answer_value: 'Test answer',
          options: null
        }
      ],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    })
  }),

  http.post('http://localhost:8000/api/insights/daily/generate', () => {
    return HttpResponse.json({
      response: 'Generated daily insight content',
      agent_type: 'daily_summary',
      session_id: 'test-session-123',
      actor_id: 'test_actor_001'
    })
  })
]
