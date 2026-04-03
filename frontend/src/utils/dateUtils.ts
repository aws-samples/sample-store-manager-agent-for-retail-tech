export const formatDate = (date: Date): string => {
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  });
};

export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatDateTime = (date: Date): string => {
  return `${formatDate(date)} ${formatTime(date)}`;
};

export const getTodayString = (): string => {
  return formatDate(new Date());
};

export const isToday = (date: string): boolean => {
  const today = new Date().toDateString();
  const targetDate = new Date(date).toDateString();
  return today === targetDate;
};