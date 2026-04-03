import { api } from './api';

// 型定義
export interface AdminMessage {
  admin_messages_id: string;
  title: string;
  content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminQuestion {
  admin_survey_id: string;
  question_text: string;
  question_type: string;
  options: any[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const adminApi = {
  getMessages: (params: {
    is_active: boolean;
    limit: number;
  }): Promise<{ messages: AdminMessage[] }> =>
    api.get('/api/admin/messages', params),

  getMessageById: (messageId: string): Promise<AdminMessage> =>
    api.get(`/api/admin/messages/${messageId}`),

  createMessage: (data: {
    title: string;
    content: string;
    is_active: boolean;
  }): Promise<{ admin_messages_id: string; message: string }> =>
    api.post('/api/admin/messages', data),

  updateMessage: (messageId: string, data: {
    title: string;
    content: string;
    is_active: boolean;
  }): Promise<{ admin_messages_id: string; message: string }> =>
    api.put(`/api/admin/messages/${messageId}`, data),

  deleteMessage: (messageId: string): Promise<{ admin_messages_id: string; message: string }> =>
    api.delete(`/api/admin/messages/${messageId}`),

  getQuestions: (params: {
    is_active: boolean;
    limit: number;
  }): Promise<{ questions: AdminQuestion[] }> =>
    api.get('/api/admin/survey/questions', params),

  getQuestionById: (questionId: string): Promise<AdminQuestion> =>
    api.get(`/api/admin/survey/questions/${questionId}`),

  createQuestion: (data: {
    question_text: string;
    question_type: string;
    options: any[];
    is_active: boolean;
  }): Promise<{ admin_survey_id: string; message: string }> =>
    api.post('/api/admin/survey/questions', data),

  updateQuestion: (questionId: string, data: {
    question_text: string;
    question_type: string;
    options: any[];
    is_active: boolean;
  }): Promise<{ admin_survey_id: string; message: string }> =>
    api.put(`/api/admin/survey/questions/${questionId}`, data),

  deleteQuestion: (questionId: string): Promise<{ admin_survey_id: string; message: string }> =>
    api.delete(`/api/admin/survey/questions/${questionId}`),
};
