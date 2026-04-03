import { create } from 'zustand';
import type { AppState, Answer, ChatMessage, Report } from '../types';
import type { ChatSession } from '../types/api';
import { localStorage } from '../utils/localStorage';

interface NotificationState {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
}

interface AppStoreActions {
  setSidebarCollapsed: (collapsed: boolean) => void;
  addAnswer: (answer: Answer) => void;
  updateAnswer: (answer: Answer) => void;
  addChatMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  saveReport: (report: Report) => void;
  loadStoredData: () => void;
  clearAnswers: () => void;
  clearChatHistory: () => void;
  showNotification: (message: string, severity?: 'success' | 'error' | 'warning' | 'info') => void;
  hideNotification: () => void;
  setChatSession: (session: ChatSession | null) => void;
  getChatSession: () => ChatSession | null;
  setUser: (user: { name: string; store: string; email: string; userId: string } | null) => void;
  reset: () => void;
}

export const useAppStore = create<AppState & AppStoreActions & { notification: NotificationState; isInitialized: boolean; chatSession: ChatSession | null }>((set, get) => ({
  user: null,
  sidebarCollapsed: false,
  currentAnswers: [],
  chatHistory: [],
  reports: [],
  loading: false,
  supplementComment: '',
  isInitialized: false,
  chatSession: null,
  notification: {
    open: false,
    message: '',
    severity: 'success',
  },

  // Actions
  setSidebarCollapsed: (collapsed: boolean) => 
    set({ sidebarCollapsed: collapsed }),

  addAnswer: (answer: Answer) => 
    set((state) => {
      const newAnswers = [...state.currentAnswers.filter(a => a.question_id !== answer.question_id), answer];
      localStorage.saveAnswers(newAnswers);
      return { currentAnswers: newAnswers };
    }),

  updateAnswer: (answer: Answer) => 
    set((state) => {
      const existingIndex = state.currentAnswers.findIndex(
        (a) => a.question_id === answer.question_id
      );

      let newAnswers;
      if (existingIndex >= 0) {
        newAnswers = [...state.currentAnswers];
        newAnswers[existingIndex] = answer;
      } else {
        newAnswers = [...state.currentAnswers, answer];
      }
      
      localStorage.saveAnswers(newAnswers);
      return { currentAnswers: newAnswers };
    }),

  addChatMessage: (message: ChatMessage) => 
    set((state) => {
      const newChatHistory = [...state.chatHistory, message];
      localStorage.saveChatHistory(newChatHistory);
      return { chatHistory: newChatHistory };
    }),

  setLoading: (loading: boolean) => 
    set({ loading }),

  setSupplementComment: (comment: string) =>
    set({ supplementComment: comment }),

  saveReport: (report: Report) => 
    set((state) => {
      const newReports = [...state.reports.filter(r => r.id !== report.id), report];
      localStorage.saveReports(newReports);
      return { reports: newReports };
    }),

  loadStoredData: () => {
    const answers = localStorage.loadAnswers();
    const chatHistory = localStorage.loadChatHistory();
    const reports = localStorage.loadReports();
    
    set({
      currentAnswers: answers,
      chatHistory,
      reports,
      isInitialized: true,
    });
  },

  clearAnswers: () => {
    localStorage.saveAnswers([]);
    set({ currentAnswers: [] });
  },

  clearChatHistory: () => {
    localStorage.saveChatHistory([]);
    set({ chatHistory: [], isInitialized: false });
  },

  showNotification: (message: string, severity: 'success' | 'error' | 'warning' | 'info' = 'success') =>
    set({ notification: { open: true, message, severity } }),

  hideNotification: () =>
    set((state) => ({ notification: { ...state.notification, open: false } })),

  setChatSession: (session: ChatSession | null) =>
    set({ chatSession: session }),

  getChatSession: () => get().chatSession,

  setUser: (user: { name: string; store: string; email: string; userId: string } | null) =>
    set({ user }),

  reset: () => set({
    sidebarCollapsed: false,
    currentAnswers: [],
    chatHistory: [],
    reports: [],
    loading: false,
    supplementComment: '',
    isInitialized: false,
    chatSession: null,
    notification: {
      open: false,
      message: '',
      severity: 'success',
    },
  }),
}));