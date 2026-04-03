import type { Answer, ChatMessage, Report } from '../types';

const STORAGE_KEYS = {
  ANSWERS: 'daily-answers',
  CHAT_HISTORY: 'chat-history',
  REPORTS: 'reports',
} as const;

const isStorageAvailable = (): boolean => {
  try {
    const test = '__storage_test__';
    window.localStorage.setItem(test, test);
    window.localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
};

const handleStorageError = (_operation: string, error: unknown): void => {
  if (error instanceof DOMException && error.code === 22) {
  }
};

export const localStorage = {
  // Check if localStorage is available
  isAvailable: isStorageAvailable,

  // Answers
  saveAnswers: (answers: Answer[]): boolean => {
    if (!isStorageAvailable()) return false;
    
    try {
      const serialized = JSON.stringify(answers);
      window.localStorage.setItem(STORAGE_KEYS.ANSWERS, serialized);
      return true;
    } catch (error) {
      handleStorageError('save answers to', error);
      return false;
    }
  },

  loadAnswers: (): Answer[] => {
    if (!isStorageAvailable()) return [];
    
    try {
      const stored = window.localStorage.getItem(STORAGE_KEYS.ANSWERS);
      if (!stored) return [];
      
      const parsed = JSON.parse(stored);
      // Validate data structure
      if (Array.isArray(parsed)) {
        return parsed.filter(item => 
          item && 
          typeof item.questionId === 'string' && 
          (typeof item.value === 'string' || typeof item.value === 'number')
        );
      }
      return [];
    } catch (error) {
      handleStorageError('load answers from', error);
      return [];
    }
  },

  // Chat History
  saveChatHistory: (messages: ChatMessage[]): boolean => {
    if (!isStorageAvailable()) return false;
    
    try {
      const serialized = JSON.stringify(messages);
      window.localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, serialized);
      return true;
    } catch (error) {
      handleStorageError('save chat history to', error);
      return false;
    }
  },

  loadChatHistory: (): ChatMessage[] => {
    if (!isStorageAvailable()) return [];
    
    try {
      const stored = window.localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);
      if (!stored) return [];
      
      const parsed = JSON.parse(stored);
      // Validate data structure
      if (Array.isArray(parsed)) {
        return parsed.filter(item => 
          item && 
          typeof item.id === 'string' && 
          typeof item.sender === 'string' && 
          typeof item.message === 'string'
        );
      }
      return [];
    } catch (error) {
      handleStorageError('load chat history from', error);
      return [];
    }
  },

  // Reports
  saveReports: (reports: Report[]): boolean => {
    if (!isStorageAvailable()) return false;
    
    try {
      const serialized = JSON.stringify(reports);
      window.localStorage.setItem(STORAGE_KEYS.REPORTS, serialized);
      return true;
    } catch (error) {
      handleStorageError('save reports to', error);
      return false;
    }
  },

  loadReports: (): Report[] => {
    if (!isStorageAvailable()) return [];
    
    try {
      const stored = window.localStorage.getItem(STORAGE_KEYS.REPORTS);
      if (!stored) return [];
      
      const parsed = JSON.parse(stored);
      // Validate data structure
      if (Array.isArray(parsed)) {
        return parsed.filter(item => 
          item && 
          typeof item.id === 'string' && 
          typeof item.type === 'string' && 
          typeof item.content === 'string'
        );
      }
      return [];
    } catch (error) {
      handleStorageError('load reports from', error);
      return [];
    }
  },

  // Clear all data
  clearAll: (): boolean => {
    if (!isStorageAvailable()) return false;
    
    try {
      Object.values(STORAGE_KEYS).forEach(key => {
        window.localStorage.removeItem(key);
      });
      return true;
    } catch (error) {
      handleStorageError('clear', error);
      return false;
    }
  },

  // Get storage usage info
  getStorageInfo: (): { used: number; available: boolean } => {
    if (!isStorageAvailable()) {
      return { used: 0, available: false };
    }

    try {
      let used = 0;
      Object.values(STORAGE_KEYS).forEach(key => {
        const item = window.localStorage.getItem(key);
        if (item) {
          used += item.length;
        }
      });
      
      return { used, available: true };
    } catch (error) {
      handleStorageError('get storage info from', error);
      return { used: 0, available: false };
    }
  },
};