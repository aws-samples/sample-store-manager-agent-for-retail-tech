import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  CircularProgress,
} from '@mui/material';
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import { surveyApi } from '../services/surveyApi';
import { insightsApi } from '../services/insightsApi';
import { useAppStore } from '../stores/appStore';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`history-tabpanel-${index}`}
      aria-labelledby={`history-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAppStore();
  const [tabValue, setTabValue] = useState(0);
  const [surveyPage, setSurveyPage] = useState(1);
  const [insightsPage, setInsightsPage] = useState(1);
  const [surveyData, setSurveyData] = useState<any[]>([]);
  const [insightsData, setInsightsData] = useState<any[]>([]);
  const [surveyLoading, setSurveyLoading] = useState(false);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [surveyTotal, setSurveyTotal] = useState(0);
  const [insightsTotal, setInsightsTotal] = useState(0);
  const [surveyLoaded, setSurveyLoaded] = useState(false);
  const [insightsLoaded, setInsightsLoaded] = useState(false);
  const itemsPerPage = 30;

  useEffect(() => {
    if (tabValue === 0 && !surveyLoaded) {
      loadSurveyData();
    } else if (tabValue === 1 && !insightsLoaded) {
      loadInsightsData();
    }
  }, [tabValue]);

  useEffect(() => {
    if (surveyLoaded) {
      loadSurveyData();
    }
  }, [surveyPage]);

  useEffect(() => {
    if (insightsLoaded) {
      loadInsightsData();
    }
  }, [insightsPage]);

  const loadSurveyData = async () => {
    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    try {
      setSurveyLoading(true);
      const response = await surveyApi.getAnswers({
        page: surveyPage,
        limit: itemsPerPage,
      });
      setSurveyData(response.answers);
      setSurveyTotal(response.total_count);
      setSurveyLoaded(true);
    } catch (error) {
      console.error('Failed to load survey data:', error);
    } finally {
      setSurveyLoading(false);
    }
  };

  const loadInsightsData = async () => {
    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    try {
      setInsightsLoading(true);
      const response = await insightsApi.getDailyInsightHistory({
        page: insightsPage,
        limit: itemsPerPage,
      });
      setInsightsData(response.insights);
      setInsightsTotal(response.total_count);
      setInsightsLoaded(true);
    } catch (error) {
      console.error('Failed to load insights data:', error);
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatDateTime = (date: string | Date) => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleSurveyRowClick = (surveyId: string) => {
    navigate(`/daily-answer-detail/${surveyId}`);
  };

  const handleInsightRowClick = (insightId: string) => {
    navigate(`/daily-report/${insightId}`);
  };

  const renderSurveyTable = () => {
    const totalPages = Math.ceil(surveyTotal / itemsPerPage);

    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton 
              onClick={() => setSurveyPage(Math.max(1, surveyPage - 1))}
              disabled={surveyPage === 1}
              size="small"
              aria-label="previous page"
            >
              <ChevronLeftIcon />
            </IconButton>
            <Typography variant="body2">
              {surveyPage} / {totalPages}
            </Typography>
            <IconButton 
              onClick={() => setSurveyPage(Math.min(totalPages, surveyPage + 1))}
              disabled={surveyPage === totalPages}
              size="small"
              aria-label="next page"
            >
              <ChevronRightIcon />
            </IconButton>
          </Box>
        </Box>
        {surveyLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>作成日時</TableCell>
                  <TableCell>更新日時</TableCell>
                  <TableCell>ユーザーコード</TableCell>
                  <TableCell>店舗コード</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {surveyData?.map((item) => (
                  <TableRow
                    key={item.survey_id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleSurveyRowClick(item.survey_id)}
                  >
                    <TableCell>{formatDateTime(item.created_at)}</TableCell>
                    <TableCell>{formatDateTime(item.updated_at)}</TableCell>
                    <TableCell>{item.user_cd}</TableCell>
                    <TableCell>{item.str_cd}</TableCell>
                  </TableRow>
                )) || []}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    );
  };

  const renderInsightsTable = () => {
    const totalPages = Math.ceil(insightsTotal / itemsPerPage);

    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton 
              onClick={() => setInsightsPage(Math.max(1, insightsPage - 1))}
              disabled={insightsPage === 1}
              size="small"
              aria-label="previous page"
            >
              <ChevronLeftIcon />
            </IconButton>
            <Typography variant="body2">
              {insightsPage} / {totalPages}
            </Typography>
            <IconButton 
              onClick={() => setInsightsPage(Math.min(totalPages, insightsPage + 1))}
              disabled={insightsPage === totalPages}
              size="small"
              aria-label="next page"
            >
              <ChevronRightIcon />
            </IconButton>
          </Box>
        </Box>
        {insightsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>生成対象日</TableCell>
                  <TableCell>作成日時</TableCell>
                  <TableCell>更新日時</TableCell>
                  <TableCell>ユーザーコード</TableCell>
                  <TableCell>店舗コード</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {insightsData?.map((item) => (
                  <TableRow
                    key={item.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleInsightRowClick(item.id)}
                  >
                    <TableCell>{item.report_date ? new Date(item.report_date).toLocaleDateString('ja-JP') : ''}</TableCell>
                    <TableCell>{formatDateTime(item.created_at)}</TableCell>
                    <TableCell>{formatDateTime(item.updated_at)}</TableCell>
                    <TableCell>{item.user_cd}</TableCell>
                    <TableCell>{item.str_cd}</TableCell>
                  </TableRow>
                )) || []}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          履歴
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Daily Survey" />
          <Tab label="Daily Insights" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          Daily Survey History
        </Typography>
        {renderSurveyTable()}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Daily Insights History
        </Typography>
        {renderInsightsTable()}
      </TabPanel>
    </Container>
  );
};

export default HistoryPage;