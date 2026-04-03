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
  ListItemText,
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
  Alert,
} from '@mui/material';
import { Save as SaveIcon, Edit as EditIcon } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../stores/appStore';
import { surveyApi } from '../services/surveyApi';
import type { Answer } from '../types';

const AnswerConfirmPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { 
    currentAnswers, 
    getChatSession,
    loading, 
    setLoading, 
    updateAnswer, 
    supplementComment, 
    setSupplementComment,
    clearAnswers,
    clearChatHistory,
    setChatSession,
    user
  } = useAppStore();
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [editingAnswer, setEditingAnswer] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string | number>('');
  const [historicalAnswers, setHistoricalAnswers] = useState<Answer[]>([]);
  const [isEditingHistorical, setIsEditingHistorical] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chatSession = getChatSession();

  useEffect(() => {
    const loadData = async () => {
      setDataLoading(true);
      if (id) {
        await loadHistoricalAnswers(id);
        setIsEditingHistorical(true);
      } else {
        setIsEditingHistorical(false);
      }
      setDataLoading(false);
    };
    loadData();
  }, [id]);

  const loadHistoricalAnswers = async (surveyId: string) => {
    try {
      const response = await surveyApi.getAnswerById(surveyId);
      
      const commentAnswer = response.answers.find(
        (answer: any) => answer.question_text === 'comment'
      );
      if (commentAnswer) {
        setSupplementComment(commentAnswer.answer_value || '');
      }
      
      const formattedAnswers: Answer[] = response.answers
        .filter((answer: any) => answer.question_text !== 'comment')
        .map((answer: any) => ({
          question_id: answer.question_id,
          question_text: answer.question_text,
          question_type: answer.question_type,
          answer_value: answer.answer_value,
          options: answer.options,
        }));
      setHistoricalAnswers(formattedAnswers);
    } catch (error) {
      console.error('Failed to load historical answers:', error);
      setError('履歴データの取得に失敗しました');
    }
  };

  // 表示する回答データを決定（履歴編集時は履歴データ、新規時は現在の回答）
  const displayAnswers = isEditingHistorical ? historicalAnswers : currentAnswers;

  // 回答の編集開始
  const handleEditAnswer = (questionId: string, currentValue: string | number) => {
    setEditingAnswer(questionId);
    setEditValue(currentValue);
  };

  // 回答の編集保存
  const handleSaveEdit = () => {
    if (editingAnswer && editValue !== '') {
      if (isEditingHistorical) {
        setHistoricalAnswers(prev => 
          prev.map(answer => 
            answer.question_id === editingAnswer 
              ? { ...answer, answer_value: String(editValue) }
              : answer
          )
        );
      } else {
        const currentAnswer = currentAnswers.find(a => a.question_id === editingAnswer);
        if (currentAnswer) {
          updateAnswer({
            ...currentAnswer,
            answer_value: String(editValue),
          });
        }
      }
    }
    setEditingAnswer(null);
    setEditValue('');
  };

  // 回答の編集キャンセル
  const handleCancelEdit = () => {
    setEditingAnswer(null);
    setEditValue('');
  };

  const handleComplete = () => {
    setShowSaveDialog(true);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setShowSaveDialog(false);
      setError(null);
      
      if (isEditingHistorical && id) {
        const existingCommentAnswer = historicalAnswers.find(
          answer => answer.question_text === 'comment'
        );
        
        const answers = [
          ...historicalAnswers
            .filter(answer => answer.question_text !== 'comment')
            .map(answer => ({
              question_id: answer.question_id,
              question_text: answer.question_text,
              question_type: answer.question_type,
              answer_value: answer.answer_value,
              options: answer.options,
            })),
          {
            question_id: existingCommentAnswer?.question_id || crypto.randomUUID(),
            question_text: 'comment',
            question_type: 'text',
            answer_value: supplementComment,
            options: undefined,
          }
        ];
        
        await surveyApi.updateAnswer(id, {
          answers,
        });
        
        navigate('/history');
      } else if (chatSession) {
        const answers = [
          ...currentAnswers.map(answer => ({
            question_id: answer.question_id,
            question_text: answer.question_text,
            question_type: answer.question_type,
            answer_value: answer.answer_value,
            options: answer.options,
          })),
          {
            question_id: crypto.randomUUID(),
            question_text: 'comment',
            question_type: 'text',
            answer_value: supplementComment,
            options: undefined,
          }
        ];

        if (!user) {
          console.error('User not authenticated');
          navigate('/');
          return;
        }
        
        await surveyApi.createAnswer({
          survey_id: chatSession.survey_id,
          answers,
        });
        
        clearAnswers();
        clearChatHistory();
        setChatSession(null);
        setSupplementComment('');
        navigate('/');
      }
    } catch (error) {
      console.error('Failed to save answers:', error);
      setError('回答の保存に失敗しました。もう一度お試しください。');
    } finally {
      setLoading(false);
    }
  };

  const renderAnswerValue = (answer: Answer) => {
    const isEmpty = !answer.answer_value || 
                    answer.answer_value === '' || 
                    (answer.question_type === 'rating' && Number(answer.answer_value) === 0);

    if (editingAnswer === answer.question_id) {
      if (answer.question_type === 'rating') {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Rating
              value={Number(editValue) || 0}
              onChange={(_, newValue) => setEditValue(newValue || 0)}
              max={5}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button size="small" onClick={handleSaveEdit}>保存</Button>
              <Button size="small" onClick={handleCancelEdit}>キャンセル</Button>
            </Box>
          </Box>
        );
      } else if (answer.question_type === 'choice') {
        const options = answer.options?.split(',') || [];
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
              <Button size="small" onClick={handleSaveEdit}>保存</Button>
              <Button size="small" onClick={handleCancelEdit}>キャンセル</Button>
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
              <Button size="small" onClick={handleSaveEdit}>保存</Button>
              <Button size="small" onClick={handleCancelEdit}>キャンセル</Button>
            </Box>
          </Box>
        );
      }
    } else {
      if (isEmpty) {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body1" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              未回答
            </Typography>
            <Button
              size="small"
              startIcon={<EditIcon />}
              onClick={() => handleEditAnswer(answer.question_id, answer.answer_value)}
            >
              編集
            </Button>
          </Box>
        );
      }

      if (answer.question_type === 'rating') {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Rating value={Number(answer.answer_value) || 0} readOnly max={5} />
            <Typography variant="body2" color="text.secondary">
              ({answer.answer_value}/5)
            </Typography>
            <Button
              size="small"
              startIcon={<EditIcon />}
              onClick={() => handleEditAnswer(answer.question_id, answer.answer_value)}
            >
              編集
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
              編集
            </Button>
          </Box>
        );
      }
    }
  };
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {dataLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* ヘッダー */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {isEditingHistorical ? '履歴回答の編集' : '回答確認・編集'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {isEditingHistorical 
                ? '過去の回答内容を編集できます' 
                : '回答内容を確認し、必要に応じて編集してください'
          }
        </Typography>
        {isEditingHistorical && (
          <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
            編集中の回答ID: {id}
          </Typography>
        )}
      </Box>

      {/* 定型質問の回答 */}
      {displayAnswers.length > 0 && (
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              定型質問の回答
            </Typography>
            <List>
              {displayAnswers.map((answer, index) => (
                <React.Fragment key={answer.question_id}>
                  <ListItem sx={{ px: 0, alignItems: 'flex-start' }}>
                    <ListItemText
                      primary={
                        <Typography variant="subtitle1" sx={{ mb: 1 }}>
                          {answer.question_text}
                        </Typography>
                      }
                      secondary={
                        <Box>
                          {renderAnswerValue(answer)}
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < displayAnswers.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Box>
        </Paper>
      )}

      {/* AIチャット履歴 */}
      {chatSession && chatSession.messages.length > 0 && (
        <Paper elevation={1} sx={{ mb: 3 }}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              AIチャット履歴
            </Typography>
            <List>
              {chatSession.messages.map((message, index) => (
                <ListItem key={index} sx={{ px: 0, alignItems: 'flex-start' }}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Chip
                          label={message.role === 'user' ? 'あなた' : 'AI'}
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

      {/* 補足コメント */}
      <Paper elevation={1} sx={{ mb: 3 }}>
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            補足コメント
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="追加でお伝えしたいことがあれば入力してください..."
            value={supplementComment}
            onChange={(e) => setSupplementComment(e.target.value)}
            variant="outlined"
          />
        </Box>
      </Paper>

      {/* 完了ボタン */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
          onClick={handleComplete}
          disabled={loading}
          sx={{ minWidth: 150 }}
        >
          {loading ? '保存中...' : (isEditingHistorical ? '更新' : '完了')}
        </Button>
      </Box>

      {/* 保存確認ダイアログ */}
      <Dialog open={showSaveDialog} onClose={() => setShowSaveDialog(false)}>
        <DialogTitle>
          {isEditingHistorical ? '回答を更新しますか？' : '回答を保存しますか？'}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {isEditingHistorical 
              ? '編集された回答内容を更新します。よろしいですか？'
              : '入力された回答内容を保存します。保存後は編集できませんが、よろしいですか？'
            }
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSaveDialog(false)}>キャンセル</Button>
          <Button onClick={handleSave} variant="contained">
            {isEditingHistorical ? '更新する' : '保存する'}
          </Button>
        </DialogActions>
      </Dialog>
        </>
      )}
    </Container>
  );
};

export default AnswerConfirmPage;