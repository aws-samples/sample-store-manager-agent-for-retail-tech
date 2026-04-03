import { api } from './api';
import type { ChatSessionResponse } from '../types/api';

export interface ChatResponse {
  response: string;
  agent_type: string;
  session_id: string;
  actor_id: string;
}

export const chatApi = {
  sendMessage: (data: {
    agent_type: string;
    prompt: string;
    session_id: string;
    survey_id: string;
  }): Promise<ChatResponse> =>
    api.post('/api/chat/message', data),

  saveSession: (data: {
    survey_id: string;
    session_id: string;
  }): Promise<{ message: string }> =>
    api.post('/api/chat/session/save', data),

  getSessionBySurvey: (surveyId: string): Promise<ChatSessionResponse> =>
    api.get('/api/chat/session', { survey_id: surveyId }),
};
