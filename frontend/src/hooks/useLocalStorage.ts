import { useEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import { localStorage } from '../utils/localStorage';

export const useLocalStorage = () => {
  const { currentAnswers, chatHistory, reports, loadStoredData } = useAppStore();

  // Load data from localStorage on mount
  useEffect(() => {
    // Use the loadStoredData method to avoid duplicate additions
    loadStoredData();
  }, []); // 依存配列を空にして、マウント時のみ実行

  // Save data to localStorage when state changes
  useEffect(() => {
    localStorage.saveAnswers(currentAnswers);
  }, [currentAnswers]);

  useEffect(() => {
    localStorage.saveChatHistory(chatHistory);
  }, [chatHistory]);

  useEffect(() => {
    localStorage.saveReports(reports);
  }, [reports]);
};