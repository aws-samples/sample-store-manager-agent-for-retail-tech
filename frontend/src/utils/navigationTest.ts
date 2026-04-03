// Navigation test utility for development
export const testAllNavigation = () => {
  const routes = [
    '/',
    '/daily-answer',
    '/ai-chat',
    '/answer-confirm',
    '/daily-report',
    '/weekly-report',
    '/history',
  ];
  
  routes.forEach(route => {
    try {
      new URL(route, window.location.origin);
    } catch (error) {
    }
  });

  try {
    const testKey = '__nav_test__';
    const testValue = 'test';
    localStorage.setItem(testKey, testValue);
    localStorage.getItem(testKey);
    localStorage.removeItem(testKey);
  } catch (error) {
  }

  const breakpoints = {
    mobile: window.matchMedia('(max-width: 768px)'),
    tablet: window.matchMedia('(max-width: 1024px)'),
    desktop: window.matchMedia('(min-width: 1025px)'),
  };

  Object.entries(breakpoints).forEach(() => {
  });
};

// Auto-run in development
if (import.meta.env.DEV) {
  // Run test after a short delay to ensure DOM is ready
  setTimeout(testAllNavigation, 1000);
}