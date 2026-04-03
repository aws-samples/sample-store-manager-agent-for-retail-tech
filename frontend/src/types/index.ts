// Question types
export interface Question {
  id: string;
  type: 'rating' | 'choice' | 'text' | 'number';
  question: string;
  options?: string[];
  required: boolean;
}

// Answer types
export interface Answer {
  question_id: string;
  question_text: string;
  question_type: 'text' | 'choice' | 'rating' | 'number';
  answer_value: string;
  options?: string;
}

// Chat message types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Report types
export interface Report {
  id: string;
  type: 'daily' | 'weekly';
  date: string;
  content: string;
  feedback?: string;
  reaction?: string;
  status: 'draft' | 'completed';
}

// History item types for the new history page structure
export interface HistoryItem {
  id: string;
  createdAt: Date;
  updatedAt: Date;
  type: '週報' | '日報' | 'ヒアリング';
  title: string;
  createdBy: string;
  store: string;
}

// App state types
export interface AppState {
  user: {
    name: string;
    store: string;
    email: string;
    userId: string;
  } | null;
  sidebarCollapsed: boolean;
  currentAnswers: Answer[];
  chatHistory: ChatMessage[];
  reports: Report[];
  loading: boolean;
  supplementComment: string;
  
  // Actions
  setSidebarCollapsed: (collapsed: boolean) => void;
  addAnswer: (answer: Answer) => void;
  updateAnswer: (answer: Answer) => void;
  addChatMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  saveReport: (report: Report) => void;
  setSupplementComment: (comment: string) => void;
}