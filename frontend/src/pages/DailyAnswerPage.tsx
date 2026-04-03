import React, { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Paper,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/appStore';
import { adminApi } from '../services/adminApi';
import { chatApi } from '../services/chatApi';
import RatingQuestion from '../components/forms/RatingQuestion';
import ChoiceQuestion from '../components/forms/ChoiceQuestion';
import TextQuestion from '../components/forms/TextQuestion';
import NumberQuestion from '../components/forms/NumberQuestion';
import ProgressIndicator from '../components/common/ProgressIndicator';
import type { Question } from '../types';
import { v4 as uuidv4 } from 'uuid';

const DailyAnswerPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentAnswers, updateAnswer, loadStoredData, setChatSession, user } = useAppStore();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  useEffect(() => {
    loadStoredData();
    loadQuestions();
    loadAnnouncements();
  }, [loadStoredData]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      const response = await adminApi.getQuestions({
        is_active: true,
        limit: 30,
      });
      
      const formattedQuestions: Question[] = response.questions.map(q => ({
        id: q.admin_survey_id,
        question: q.question_text,
        type: q.question_type as 'rating' | 'choice' | 'text' | 'number',
        options: q.options,
        required: false,
      }));
      
      setQuestions(formattedQuestions);
    } catch (error) {
      console.error('Failed to load questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAnnouncements = async () => {
    try {
      const response = await adminApi.getMessages({
        is_active: true,
        limit: 100,
      });
      setAnnouncements(response.messages);
    } catch (error) {
      console.error('Failed to load announcements:', error);
    }
  };

  const getAnswerValue = (questionId: string): string | number => {
    const answer = currentAnswers.find(a => a.question_id === questionId);
    if (!answer) {
      const question = questions.find(q => q.id === questionId);
      return question?.type === 'rating' ? 0 : '';
    }
    const question = questions.find(q => q.id === questionId);
    if (question?.type === 'rating') {
      return Number(answer.answer_value) || 0;
    }
    return answer.answer_value;
  };

  const getAnsweredCount = (): number => {
    return questions.filter(question => {
      const value = getAnswerValue(question.id);
      if (question.type === 'rating') {
        return typeof value === 'number' && value > 0;
      }
      return value !== '';
    }).length;
  };

  const generatePromptFromAnswers = (): string => {
    const answersText = questions.map(question => {
      const value = getAnswerValue(question.id);
      return `${question.question}: ${value}`;
    }).join('\n');
    
    return `以下の定型質問への回答を基に、詳細なヒアリングを開始してください。\n\n${answersText}`;
  };

  const handleNext = async () => {
    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    try {
      setSubmitting(true);

      questions.forEach(question => {
        const existingAnswer = currentAnswers.find(a => a.question_id === question.id);
        if (!existingAnswer) {
          updateAnswer({
            question_id: question.id,
            question_text: question.question,
            question_type: question.type as 'text' | 'choice' | 'rating' | 'number',
            answer_value: question.type === 'rating' ? '0' : '',
            options: question.options?.join(','),
          });
        }
      });

      const sessionId = uuidv4();
      const surveyId = uuidv4();
      const prompt = generatePromptFromAnswers();

      const response = await chatApi.sendMessage({
        agent_type: 'hearing',
        prompt,
        session_id: sessionId,
        survey_id: surveyId,
      });

      setChatSession({
        session_id: response.session_id,
        actor_id: response.actor_id,
        survey_id: surveyId,
        messages: [
          { role: 'user', content: prompt, timestamp: new Date() },
          { role: 'assistant', content: response.response, timestamp: new Date() },
        ],
      });

      setShowSuccessMessage(true);
      setTimeout(() => {
        navigate('/ai-chat');
      }, 1500);
    } catch (error) {
      console.error('Failed to start AI chat:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAnswerChange = (questionId: string, value: string | number) => {
    const question = questions.find(q => q.id === questionId);
    if (!question) {
      console.error('Question not found:', questionId);
      return;
    }

    try {
      const answerValue = value === null || value === undefined ? '' : String(value);
      
      updateAnswer({
        question_id: questionId,
        question_text: question.question,
        question_type: question.type as 'text' | 'choice' | 'rating' | 'number',
        answer_value: answerValue,
        options: question.options?.join(','),
      });
    } catch (error) {
      console.error('Failed to save answer:', error);
    }
  };

  const renderQuestion = (question: Question) => {
    const value = getAnswerValue(question.id);

    switch (question.type) {
      case 'rating':
        return (
          <RatingQuestion
            key={question.id}
            question={question.question}
            value={typeof value === 'number' ? value : 0}
            onChange={(newValue) => handleAnswerChange(question.id, newValue || 0)}
            required={question.required}
          />
        );
      case 'choice':
        return (
          <ChoiceQuestion
            key={question.id}
            question={question.question}
            options={question.options || []}
            value={typeof value === 'string' ? value : ''}
            onChange={(newValue) => handleAnswerChange(question.id, newValue)}
            required={question.required}
          />
        );
      case 'text':
        return (
          <TextQuestion
            key={question.id}
            question={question.question}
            value={typeof value === 'string' ? value : ''}
            onChange={(newValue) => handleAnswerChange(question.id, newValue)}
            required={question.required}
          />
        );
      case 'number':
        return (
          <NumberQuestion
            key={question.id}
            question={question.question}
            value={value}
            onChange={(newValue) => handleAnswerChange(question.id, newValue)}
            required={question.required}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          アンケート
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          今日の業務についてお聞かせください。回答は自動的に保存されます。
        </Typography>
        
        <ProgressIndicator
          current={getAnsweredCount()}
          total={questions.length}
          label="回答進捗"
        />
      </Box>

      {announcements.length > 0 && (
        <Paper sx={{ p: 3, mb: 3, backgroundColor: '#fff3cd', borderLeft: '4px solid #ffc107' }}>
          <Typography variant="h6" sx={{ mb: 2, color: '#856404' }}>
            店舗へのお知らせ
          </Typography>
          {announcements.map((announcement) => (
            <Typography key={announcement.admin_messages_id} variant="body1" sx={{ color: '#856404', mb: 1 }}>
              {announcement.content}
            </Typography>
          ))}
        </Paper>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Paper elevation={1} sx={{ p: 3, mb: 4 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {questions.map(renderQuestion)}
            </Box>
          </Paper>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleNext}
              disabled={submitting}
              sx={{
                minWidth: 120,
                py: 1.5,
              }}
            >
              {submitting ? <CircularProgress size={24} /> : '次へ'}
            </Button>
          </Box>
        </>
      )}

      <Snackbar
        open={showSuccessMessage}
        autoHideDuration={1500}
        onClose={() => setShowSuccessMessage(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="success" sx={{ width: '100%' }}>
          回答を保存しました！AIチャットに移動します...
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default DailyAnswerPage;