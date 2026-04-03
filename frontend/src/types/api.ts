export interface ApiError {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
  }> | string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total_count: number;
  current_page: number;
  total_pages: number;
  limit: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatSession {
  session_id: string;
  actor_id: string;
  survey_id: string;
  messages: ChatMessage[];
}

export interface ChatSessionResponse {
  session_id: string;
  survey_id: string;
  user_cd: string;
  str_cd: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
    agent_type?: string;
  }>;
  created_at: string;
}

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}
