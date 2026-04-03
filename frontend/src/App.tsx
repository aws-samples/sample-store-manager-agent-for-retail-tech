import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { useEffect } from 'react';
import { useLocalStorage } from './hooks/useLocalStorage';
import { useAppStore } from './stores/appStore';
import { useAuth } from './contexts/AuthContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import NotificationSnackbar from './components/common/NotificationSnackbar';
import AppLayout from './components/layout/AppLayout';
import TopPage from './pages/TopPage';
import DailyAnswerPage from './pages/DailyAnswerPage';
import AIChatPage from './pages/AIChatPage';
import AnswerConfirmPage from './pages/AnswerConfirmPage';
import DailyReportPage from './pages/DailyReportPage';
import HistoryPage from './pages/HistoryPage';
import DailyAnswerDetailPage from './pages/DailyAnswerDetailPage';
import AdminPage from './pages/AdminPage';
import './utils/navigationTest';
import './utils/finalValidation';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
    ].join(','),
  },
});

const selfSignUpEnabled = import.meta.env.VITE_APP_SELF_SIGN_UP_ENABLED === 'true';

function App() {
  useLocalStorage();
  const { notification, hideNotification, setUser } = useAppStore();
  const { user: authUser, loading } = useAuth();

  useEffect(() => {
    if (authUser && authUser.groups.length > 0) {
      setUser({
        name: authUser.username,
        store: authUser.groups[0],
        email: authUser.email,
        userId: authUser.userId,
      });
    } else if (!authUser) {
      setUser(null);
    }
  }, [authUser, setUser]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          backgroundColor: '#f5f5f5',
        }}
      >
        <Authenticator
          initialState="signIn"
          loginMechanisms={['email']}
          hideSignUp={!selfSignUpEnabled}
          components={{
            SignIn: {
              Header() {
                return (
                  <h3 style={{
                    textAlign: 'center',
                    color: '#1976d2',
                    marginBottom: '20px'
                  }}>
                    Sign In
                  </h3>
                );
              },
            },
            SignUp: {
              Header() {
                return (
                  <h3 style={{
                    textAlign: 'center',
                    color: '#1976d2',
                    marginBottom: '20px'
                  }}>
                    Create Account
                  </h3>
                );
              },
            }
          }}
        >
          {() => {
            if (loading) {
              return (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
                  <div>Loading...</div>
                </Box>
              );
            }
            
            return (
              <ErrorBoundary>
                <Router>
                  <Routes>
                    <Route path="/" element={<AppLayout />}>
                      <Route index element={<TopPage />} />
                      <Route path="daily-answer" element={<DailyAnswerPage />} />
                      <Route path="ai-chat" element={<AIChatPage />} />
                      <Route path="answer-confirm" element={<AnswerConfirmPage />} />
                      <Route path="answer-confirm/:id" element={<AnswerConfirmPage />} />
                      <Route path="daily-report" element={<DailyReportPage />} />
                      <Route path="daily-report/:id" element={<DailyReportPage />} />
                      <Route path="history" element={<HistoryPage />} />
                      <Route path="admin" element={<AdminPage />} />
                      <Route path="daily-answer-detail/:id" element={<DailyAnswerDetailPage />} />
                    </Route>
                  </Routes>
                </Router>
                
                <NotificationSnackbar
                  open={notification.open}
                  message={notification.message}
                  severity={notification.severity}
                  onClose={hideNotification}
                />
              </ErrorBoundary>
            );
          }}
        </Authenticator>
      </Box>
    </ThemeProvider>
  );
}

export default App;
