import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  List,
  ListItem,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Rating,
  FormControl,
  RadioGroup,
  FormControlLabel,
  Radio,
  CircularProgress,
  ListItemText,
} from '@mui/material';
import { Save as SaveIcon, Edit as EditIcon } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../stores/appStore';
import { surveyApi } from '../services/surveyApi';
import { chatApi } from '../services/chatApi';

const DailyAnswerDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { 
    loading, 
    setLoading, 
    getChatSession,
    setChatSession
  } = useAppStore();
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [editingAnswer, setEditingAnswer] = useState<string | number | null>(null);
  const [editValue, setEditValue] = useState<string | number>('');
  const [surveyData, setSurveyData] = useState<any>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [modifiedQuestionIds, setModifiedQuestionIds] = useState<Set<string>>(new Set());
  const chatSession = getChatSession();

  useEffect(() => {
    if (id) {
      loadSurveyData(id);
    }
  }, [id]);

  const loadSurveyData = async (surveyId: string) => {
    try {
      setPageLoading(true);
      const surveyResponse = await surveyApi.getAnswerById(surveyId);
      
      setSurveyData(surveyResponse);

      const existingSession = getChatSession();

      if (existingSession && existingSession.survey_id === surveyId) {
        // Store has the correct session for this survey — no API call needed
      } else if (surveyId) {
        try {
          const sessionData = await chatApi.getSessionBySurvey(surveyId);
          const formattedSession = {
            session_id: sessionData.session_id,
            actor_id: sessionData.user_cd,
            survey_id: sessionData.survey_id,
            messages: sessionData.messages.map((msg: any) => ({
              role: msg.role,
              content: msg.content,
              timestamp: new Date(msg.timestamp),
            })),
          };
          setChatSession(formattedSession);
        } catch (sessionError) {
          console.warn('Chat session not found for survey:', surveyId, sessionError);
          setChatSession(null);
        }
      }
    } catch (error) {
      console.error('Failed to load survey data:', error);
    } finally {
      setPageLoading(false);
    }
  };

  // Start editing answer
  const handleEditAnswer = (questionId: string, currentValue: string | number) => {
    setEditingAnswer(questionId);
    setEditValue(currentValue);
  };

  // Save edited answer
  const handleSaveEdit = () => {
    if (editingAnswer && editValue !== '' && surveyData) {
      const updatedAnswers = surveyData.answers.map((answer: any) =>
        answer.question_id === editingAnswer
          ? { ...answer, answer_value: editValue }
          : answer
      );
      setSurveyData({ ...surveyData, answers: updatedAnswers });
      setModifiedQuestionIds(prev => new Set(prev).add(editingAnswer as string));
    }
    setEditingAnswer(null);
    setEditValue('');
  };

  // Cancel editing answer
  const handleCancelEdit = () => {
    setEditingAnswer(null);
    setEditValue('');
  };

  // Start editing supplement comment
  const handleEditComment = () => {
    const commentAnswer = surveyData?.answers.find(
      (answer: any) => answer.question_text === 'comment'
    );
    if (commentAnswer) {
      setEditingAnswer(commentAnswer.question_id);
      setEditValue(commentAnswer.answer_value || '');
    }
  };

  // Complete handler
  const handleComplete = () => {
    setShowSaveDialog(true);
  };

  const handleSave = async () => {
    if (!id || !surveyData) return;
    
    try {
      setLoading(true);
      setShowSaveDialog(false);
      
      const answers = surveyData.answers
        .filter((answer: any) => modifiedQuestionIds.has(answer.question_id))
        .map((answer: any) => ({
          question_id: answer.question_id,
          question_text: answer.question_text,
          question_type: answer.question_type,
          answer_value: String(answer.answer_value),
          options: answer.options || null,
        }));
      
      if (answers.length > 0) {
        await surveyApi.updateAnswer(id, { answers });
      }
      
      navigate('/history');
    } catch (error) {
      console.error('Failed to save answers:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderAnswerValue = (answer: any) => {
    if (editingAnswer === answer.question_id) {
      if (answer.question_type === 'rating') {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Rating
              value={editValue as number}
              onChange={(_, newValue) => setEditValue(newValue || 0)}
              max={5}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button size="small" onClick={handleSaveEdit}>Apply</Button>
              <Button size="small" onClick={handleCancelEdit}>Cancel</Button>
            </Box>
          </Box>
        );
      } else if (answer.question_type === 'choice') {
        const options = answer.options ? answer.options.split(',') : [];
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <FormControl component="fieldset">
              <RadioGroup
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
              >
                {options.map((option: string) => (
                  <FormControlLabel
                    key={option}
                    value={option}
                    control={<Radio />}
                    label={option}
                  />
                ))}
              </RadioGroup>
            </FormControl>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button size="small" onClick={handleSaveEdit}>Apply</Button>
              <Button size="small" onClick={handleCancelEdit}>Cancel</Button>
            </Box>
          </Box>
        );
      } else {
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              rows={3}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              size="small"
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button size="small" onClick={handleSaveEdit}>Apply</Button>
              <Button size="small" onClick={handleCancelEdit}>Cancel</Button>
            </Box>
          </Box>
        );
      }
    } else {
      if (answer.question_type === 'rating') {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Rating value={Number(answer.answer_value)} readOnly max={5} />
            <Typography variant="body2" color="text.secondary">
              ({answer.answer_value}/5)
            </Typography>
            <Button
              size="small"
              startIcon={<EditIcon />}
              onClick={() => handleEditAnswer(answer.question_id, Number(answer.answer_value))}
            >
              Edit
            </Button>
          </Box>
        );
      } else {
        return (
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Typography variant="body1" sx={{ flex: 1 }}>
              {answer.answer_value}
            </Typography>
            <Button
              size="small"
              startIcon={<EditIcon />}
              onClick={() => handleEditAnswer(answer.question_id, answer.answer_value)}
            >
              Edit
            </Button>
          </Box>
        );
      }
    }
  };

  // Format time
  const formatTime = (timestamp: string) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(timestamp));
  };

  if (pageLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Review & Edit Answers
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Review your past answers and edit if needed
        </Typography>
        {id && (
          <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
            Editing answer ID: {id}
          </Typography>
        )}
      </Box>

      {/* Survey Answers */}
      {surveyData?.answers && surveyData.answers.length > 0 && (
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Survey Answers
            </Typography>
            <List>
              {surveyData.answers
                .filter((answer: any) => answer.question_text !== 'comment')
                .map((answer: any, index: number) => (
                <React.Fragment key={answer.question_id}>
                  <ListItem sx={{ px: 0, py: 2, alignItems: 'flex-start' }}>
                    <Box sx={{ width: '100%' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'medium', flex: 1 }}>
                          {answer.question_text}
                        </Typography>
                        <Chip 
                          label={formatTime(surveyData.created_at)} 
                          size="small" 
                          variant="outlined"
                          sx={{ ml: 2 }}
                        />
                      </Box>
                      <Box sx={{ mt: 1 }}>
                        {renderAnswerValue(answer)}
                      </Box>
                    </Box>
                  </ListItem>
                  {index < surveyData.answers.filter((a: any) => a.question_text !== 'comment').length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Box>
        </Paper>
      )}

      {chatSession && chatSession.messages.length > 0 && (
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              AI Chat History
            </Typography>
            <List>
              {chatSession.messages.map((message, index) => (
                <ListItem key={index} sx={{ px: 0, alignItems: 'flex-start' }}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Chip
                          label={message.role === 'user' ? 'You' : 'AI'}
                          size="small"
                          color={message.role === 'user' ? 'primary' : 'secondary'}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {new Intl.DateTimeFormat('ja-JP', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          }).format(message.timestamp)}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        </Paper>
      )}

      {/* Supplement Comment */}
      <Paper elevation={1} sx={{ mb: 3 }}>
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Supplement Comment
          </Typography>
          {(() => {
            const commentAnswer = surveyData?.answers.find(
              (answer: any) => answer.question_text === 'comment'
            );
            
            if (editingAnswer === commentAnswer?.question_id) {
              return (
                <Box>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    placeholder="Enter any additional comments..."
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    variant="outlined"
                    sx={{ mb: 1 }}
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button size="small" onClick={handleSaveEdit}>Apply</Button>
                    <Button size="small" onClick={handleCancelEdit}>Cancel</Button>
                  </Box>
                </Box>
              );
            } else {
              return (
                <Box>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
                    {commentAnswer?.answer_value || '(No supplement comment)'}
                  </Typography>
                  <Button
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={handleEditComment}
                  >
                    Edit
                  </Button>
                </Box>
              );
            }
          })()}
        </Box>
      </Paper>

      {/* アクションボタン */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
          onClick={handleComplete}
          disabled={loading}
          sx={{ minWidth: 200 }}
        >
          {loading ? 'Saving...' : 'Save & Complete'}
        </Button>
      </Box>

      {/* 保存確認ダイアログ */}
      <Dialog open={showSaveDialog} onClose={() => setShowSaveDialog(false)}>
        <DialogTitle>Save answers?</DialogTitle>
        <DialogContent>
          <Typography>
            Your edited answers will be saved. Are you sure?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSaveDialog(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DailyAnswerDetailPage;
