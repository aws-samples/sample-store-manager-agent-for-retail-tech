import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
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
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { adminApi } from '../services/adminApi';
import { useAppStore } from '../stores/appStore';

// Local type definitions
interface AdminMessage {
  admin_messages_id: string;
  title: string;
  content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AdminQuestion {
  admin_survey_id: string;
  question_text: string;
  question_type: string;
  options: any[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const AdminPage: React.FC = () => {
  const user = useAppStore((state) => state.user);

  if (user?.store !== 'admin') {
    return <Navigate to="/" replace />;
  }

  const [questions, setQuestions] = useState<AdminQuestion[]>([]);
  const [notices, setNotices] = useState<AdminMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [questionDialog, setQuestionDialog] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<AdminQuestion | null>(null);
  const [newQuestion, setNewQuestion] = useState({ 
    question_text: '', 
    question_type: 'text', 
    options: [] as string[] 
  });
  const [optionsInput, setOptionsInput] = useState('');

  const [noticeDialog, setNoticeDialog] = useState(false);
  const [editingNotice, setEditingNotice] = useState<AdminMessage | null>(null);
  const [newNotice, setNewNotice] = useState({ title: '', content: '' });

  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ type: 'question' | 'notice', id: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [questionsRes, noticesRes] = await Promise.all([
        adminApi.getQuestions({ is_active: true, limit: 100 }),
        adminApi.getMessages({ is_active: true, limit: 100 })
      ]);
      setQuestions(questionsRes.questions);
      setNotices(noticesRes.messages);
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuestion = async () => {
    try {
      setSaving(true);
      const data: any = {
        question_text: newQuestion.question_text,
        question_type: newQuestion.question_type,
        is_active: true,
      };

      if (newQuestion.question_type === 'choice') {
        data.options = optionsInput.split(',').map(o => o.trim()).filter(o => o);
      }

      if (editingQuestion) {
        await adminApi.updateQuestion(editingQuestion.admin_survey_id, data);
      } else {
        await adminApi.createQuestion(data);
      }

      await loadData();
      setQuestionDialog(false);
      setEditingQuestion(null);
      setNewQuestion({ question_text: '', question_type: 'text', options: [] });
      setOptionsInput('');
    } catch (err) {
      setError('Failed to save question');
    } finally {
      setSaving(false);
    }
  };

  const handleEditQuestion = (question: AdminQuestion) => {
    setEditingQuestion(question);
    setNewQuestion({
      question_text: question.question_text,
      question_type: question.question_type,
      options: question.options || [],
    });
    setOptionsInput((question.options || []).join(', '));
    setQuestionDialog(true);
  };

  const handleDeleteQuestion = async (id: string) => {
    setDeleteTarget({ type: 'question', id });
    setDeleteDialog(true);
  };

  const handleSaveNotice = async () => {
    try {
      setSaving(true);
      const data = {
        title: newNotice.title,
        content: newNotice.content,
        is_active: true,
      };

      if (editingNotice) {
        await adminApi.updateMessage(editingNotice.admin_messages_id, data);
      } else {
        await adminApi.createMessage(data);
      }

      await loadData();
      setNoticeDialog(false);
      setEditingNotice(null);
      setNewNotice({ title: '', content: '' });
    } catch (err) {
      setError('Failed to save announcement');
    } finally {
      setSaving(false);
    }
  };

  const handleEditNotice = (notice: AdminMessage) => {
    setEditingNotice(notice);
    setNewNotice({ title: notice.title, content: notice.content });
    setNoticeDialog(true);
  };

  const handleDeleteNotice = async (id: string) => {
    setDeleteTarget({ type: 'notice', id });
    setDeleteDialog(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      setDeleting(true);
      if (deleteTarget.type === 'question') {
        await adminApi.deleteQuestion(deleteTarget.id);
      } else {
        await adminApi.deleteMessage(deleteTarget.id);
      }
      await loadData();
      setDeleteDialog(false);
      setDeleteTarget(null);
    } catch (err) {
      setError(`Failed to delete ${deleteTarget.type === 'question' ? 'question' : 'announcement'}`);
      setDeleteDialog(false);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Admin
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="h6">Announcements</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setNoticeDialog(true)}
              >
                Add Announcement
              </Button>
            </Box>

            <List>
              {notices.map((notice) => (
                <ListItem 
                  key={notice.admin_messages_id} 
                  divider
                  sx={{
                    flexDirection: { xs: 'column', sm: 'row' },
                    alignItems: { xs: 'flex-start', sm: 'center' },
                    gap: { xs: 1, sm: 0 }
                  }}
                >
                  <ListItemText
                    primary={notice.title}
                    secondary={
                      <Box>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            mb: 1,
                            wordBreak: 'break-word',
                            overflowWrap: 'break-word'
                          }}
                        >
                          {notice.content.length > 50 ? `${notice.content.substring(0, 50)}...` : notice.content}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(notice.created_at).toLocaleDateString()}
                        </Typography>
                      </Box>
                    }
                    sx={{ pr: { xs: 0, sm: 10 } }}
                  />
                  <ListItemSecondaryAction
                    sx={{
                      position: { xs: 'relative', sm: 'absolute' },
                      right: { xs: 'auto', sm: 16 },
                      transform: { xs: 'none', sm: 'translateY(-50%)' },
                      top: { xs: 'auto', sm: '50%' }
                    }}
                  >
                    <IconButton onClick={() => handleEditNotice(notice)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton onClick={() => handleDeleteNotice(notice.admin_messages_id)}>
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>

        <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Survey Questions</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setQuestionDialog(true)}
              >
                Add Question
              </Button>
            </Box>

            <List>
              {questions.map((question) => (
                <ListItem key={question.admin_survey_id} divider>
                  <ListItemText
                    primary={question.question_text}
                    secondary={
                      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <Chip label={question.question_type} size="small" />
                        {question.options && question.options.length > 0 && (
                          <Chip label={`Options: ${question.options.length}`} size="small" variant="outlined" />
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton onClick={() => handleEditQuestion(question)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton onClick={() => handleDeleteQuestion(question.admin_survey_id)}>
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>
      </Box>

      <Dialog open={questionDialog} onClose={() => setQuestionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingQuestion ? 'Edit Question' : 'Add Question'}</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Question Text"
            value={newQuestion.question_text}
            onChange={(e) => setNewQuestion(prev => ({ ...prev, question_text: e.target.value }))}
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Answer Type</InputLabel>
            <Select
              value={newQuestion.question_type}
              onChange={(e) => setNewQuestion(prev => ({ ...prev, question_type: e.target.value }))}
            >
              <MenuItem value="text">Text</MenuItem>
              <MenuItem value="choice">Choice</MenuItem>
              <MenuItem value="rating">Rating</MenuItem>
              <MenuItem value="number">Number</MenuItem>
            </Select>
          </FormControl>
          {newQuestion.question_type === 'choice' && (
            <TextField
              fullWidth
              label="Options (comma-separated)"
              value={optionsInput}
              onChange={(e) => setOptionsInput(e.target.value)}
              margin="normal"
              placeholder="Option 1, Option 2, Option 3"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQuestionDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleSaveQuestion} 
            variant="contained"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={noticeDialog} onClose={() => setNoticeDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingNotice ? 'Edit Announcement' : 'Add Announcement'}</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Title"
            value={newNotice.title}
            onChange={(e) => setNewNotice(prev => ({ ...prev, title: e.target.value }))}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Content"
            value={newNotice.content}
            onChange={(e) => setNewNotice(prev => ({ ...prev, content: e.target.value }))}
            margin="normal"
            multiline
            rows={4}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoticeDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleSaveNotice} 
            variant="contained"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Are you sure you want to delete?</DialogTitle>
        <DialogContent>
          <Typography>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleConfirmDelete} 
            variant="contained" 
            color="error"
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={20} /> : null}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminPage;
