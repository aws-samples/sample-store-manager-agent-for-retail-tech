import { api } from './api';

export interface SurveyAnswer {
  survey_id: string;
  user_cd: string;
  str_cd: string;
  answers: any[];
  session_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SurveyAnswersResponse {
  answers: SurveyAnswer[];
  total_count: number;
  current_page: number;
  total_pages: number;
  limit: number;
}

export const surveyApi = {
  getAnswers: (params: {
    page: number;
    limit: number;
  }): Promise<SurveyAnswersResponse> =>
    api.get('/api/survey/answers', params),

  getAnswerById: (surveyId: string): Promise<SurveyAnswer> =>
    api.get(`/api/survey/answers/${surveyId}`),

  createAnswer: (data: {
    survey_id: string;
    answers: any[];
  }): Promise<{ survey_id: string; message: string }> =>
    api.post('/api/survey/answers', data),

  updateAnswer: (surveyId: string, data: {
    answers: any[];
  }): Promise<{ survey_id: string; message: string }> =>
    api.put(`/api/survey/answers/${surveyId}`, data),
};
