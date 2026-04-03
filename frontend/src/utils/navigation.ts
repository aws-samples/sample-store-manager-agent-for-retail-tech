import type { NavigateFunction } from 'react-router-dom';

export interface NavigationItem {
  path: string;
  label: string;
  requiresAnswers?: boolean;
  requiresReports?: boolean;
}

export const navigationItems: NavigationItem[] = [
  { path: '/', label: 'ホーム' },
  { path: '/daily-answer', label: '日次回答' },
  { path: '/ai-chat', label: 'AIチャット', requiresAnswers: true },
  { path: '/answer-confirm', label: '回答確認', requiresAnswers: true },
  { path: '/daily-report', label: '日報' },
  { path: '/weekly-report', label: '週報' },
  { path: '/history', label: '履歴' },
];

export const validateNavigation = (
  targetPath: string,
  currentAnswers: any[],
  reports: any[]
): { canNavigate: boolean; reason?: string } => {
  const item = navigationItems.find(nav => nav.path === targetPath);
  
  if (!item) {
    return { canNavigate: true };
  }

  if (item.requiresAnswers && currentAnswers.length === 0) {
    return { 
      canNavigate: false, 
      reason: '日次回答を完了してからアクセスしてください。' 
    };
  }

  if (item.requiresReports && reports.length === 0) {
    return { 
      canNavigate: false, 
      reason: '日報または週報を作成してからアクセスしてください。' 
    };
  }

  return { canNavigate: true };
};

export const safeNavigate = (
  navigate: NavigateFunction,
  targetPath: string,
  currentAnswers: any[],
  reports: any[],
  showNotification: (message: string, severity?: 'error' | 'warning') => void
): boolean => {
  const validation = validateNavigation(targetPath, currentAnswers, reports);
  
  if (validation.canNavigate) {
    navigate(targetPath);
    return true;
  } else {
    showNotification(validation.reason || 'アクセスできません', 'warning');
    return false;
  }
};