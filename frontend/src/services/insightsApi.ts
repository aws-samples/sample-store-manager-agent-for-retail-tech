import { api } from './api';

export interface DailyInsight {
  id: string;
  user_cd: string;
  str_cd: string;
  report_date: string;
  status: string;
  report_text: string;
  session_id: string;
  actor_id: string;
  created_at: string;
  updated_at: string;
  supplement_comment?: string;
  user_feedback?: string;
}

export interface DailyInsightsHistoryResponse {
  insights: DailyInsight[];
  total_count: number;
  current_page: number;
  total_pages: number;
}

export interface GenerateInsightResponse {
  response: string;
  agent_type: string;
  session_id: string;
  actor_id: string;
  summary_id: string;
}

export const insightsApi = {
  getDailyInsight: (params: {
    report_date: string;
  }): Promise<DailyInsight> =>
    api.get('/api/insights/daily', params),

  generateDailyInsight: (data: {
    agent_type: string;
    prompt: string;
    session_id: string;
    report_date: string;
  }): Promise<GenerateInsightResponse> =>
    api.post('/api/insights/daily/generate', data),

  updateDailyInsight: (insightId: string, data: {
    report_date: string;
    status: string;
    report_text: string;
    session_id: string;
  }): Promise<{ message: string }> =>
    api.put(`/api/insights/daily/${insightId}`, data),

  updateFeedback: (insightId: string, data: {
    user_feedback: string;
  }): Promise<{ message: string }> =>
    api.put(`/api/insights/daily/${insightId}/feedback`, data),

  createDailyInsight: (insightId: string, data: {
    report_date: string;
    status: string;
    report_text: string;
    session_id: string;
  }): Promise<{ message: string }> =>
    api.put(`/api/insights/daily/${insightId}`, data),

  getDailyInsightHistory: (params: {
    page: number;
    limit: number;
  }): Promise<DailyInsightsHistoryResponse> =>
    api.get('/api/insights/daily/history', params),

  getDailyInsightById: (insightId: string): Promise<DailyInsight> =>
    api.get(`/api/insights/daily/${insightId}`),
};
