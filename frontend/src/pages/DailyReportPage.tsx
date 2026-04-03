import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  CardActions,
  Alert,
  CircularProgress,
  Backdrop,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../stores/appStore';
import { insightsApi } from '../services/insightsApi';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ConfirmDialog from '../components/common/ConfirmDialog';
import AiEditInstructionBox from '../components/common/AiEditInstructionBox';
import { v4 as uuidv4 } from 'uuid';

const DailyReportPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const { user } = useAppStore();
  
  const [reportContent, setReportContent] = useState('');
  const [currentInsight, setCurrentInsight] = useState<any>(null);
  const [displayDate, setDisplayDate] = useState<string>('');
  const [selectedFeedback, setSelectedFeedback] = useState<string>('');
  const [userComment, setUserComment] = useState('');
  const [showAiChat, setShowAiChat] = useState(false);
  const [aiChatMessage, setAiChatMessage] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showReactionSaveDialog, setShowReactionSaveDialog] = useState(false);
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);
  const [regeneratingReport, setRegeneratingReport] = useState(false);
  const [processingAiEdit, setProcessingAiEdit] = useState(false);
  const [loading, setPageLoading] = useState(true);
  const [sessionId, setSessionId] = useState<string>('');
  const [_actorId, setActorId] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isQuickSaving, setIsQuickSaving] = useState(false);
  const [isSavingReaction, setIsSavingReaction] = useState(false);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    if (hasLoadedRef.current) return;
    hasLoadedRef.current = true;
    
    loadPageData();
  }, [id]);

  const loadPageData = async () => {
    try {
      setPageLoading(true);
      if (id) {
        await loadSpecificInsight(id);
      } else {
        await loadDailyInsight();
      }
    } catch (error) {
      console.error('Failed to load page data:', error);
    } finally {
      setPageLoading(false);
    }
  };

  const loadSpecificInsight = async (insightId: string) => {
    try {
      const insight = await insightsApi.getDailyInsightById(insightId);
      setCurrentInsight(insight);
      setReportContent(insight.report_text);
      setSessionId(insight.session_id);
      setActorId(insight.actor_id);
      setUserComment(insight.user_feedback || '');
      setDisplayDate(insight.report_date);
    } catch (error) {
      console.error('Failed to load specific insight:', error);
      await loadDailyInsight();
    }
  };

  const loadDailyInsight = async () => {
    try {
      const now = new Date();
      const jstDate = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }));
      jstDate.setDate(jstDate.getDate() - 1);
      const year = jstDate.getFullYear();
      const month = String(jstDate.getMonth() + 1).padStart(2, '0');
      const day = String(jstDate.getDate()).padStart(2, '0');
      const reportDate = `${year}-${month}-${day}`;

      if (!user) {
        console.error('User not authenticated');
        navigate('/');
        return;
      }

      const insight = await insightsApi.getDailyInsight({
        report_date: reportDate,
      });

      setCurrentInsight(insight);
      setReportContent(insight.report_text);
      setSessionId(insight.session_id);
      setActorId(insight.actor_id);
      setUserComment(insight.user_feedback || '');
      setDisplayDate(reportDate);
    } catch (error) {
      console.error('No existing insight found, will generate new one');
      await generateNewInsight();
    }
  };

  const generateNewInsight = async () => {
    if (isGenerating) return;
    
    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }
    
    try {
      setIsGenerating(true);
      const newSessionId = uuidv4();
      const now = new Date();
      const jstDate = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }));
      jstDate.setDate(jstDate.getDate() - 1);
      const year = jstDate.getFullYear();
      const month = String(jstDate.getMonth() + 1).padStart(2, '0');
      const day = String(jstDate.getDate()).padStart(2, '0');
      const reportDate = `${year}-${month}-${day}`;

      const response = await insightsApi.generateDailyInsight({
        agent_type: 'daily_summary',
        prompt: '前日の業務データを基に、Daily Insightsレポートを生成してください。',
        session_id: newSessionId,
        report_date: reportDate,
      });
      
      const newInsight = {
        id: response.summary_id,
        user_cd: user.userId,
        str_cd: user.store,
        report_date: reportDate,
        status: 'draft',
        report_text: response.response,
        session_id: response.session_id,
        actor_id: response.actor_id,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setReportContent(response.response);
      setSessionId(response.session_id);
      setActorId(response.actor_id);
      setCurrentInsight(newInsight);
      setDisplayDate(reportDate);
    } catch (error) {
      console.error('Failed to generate new insight:', error);
    } finally {
      setIsGenerating(false);
    }
  };
  const handleExecuteAiEdit = () => {
    if (!aiChatMessage.trim()) return;
    
    setProcessingAiEdit(true);
    
    setTimeout(() => {
      const modifiedContent = reportContent + '\n\n## AI修正による追加\n- ' + aiChatMessage;
      setReportContent(modifiedContent);
      setProcessingAiEdit(false);
      setShowAiChat(false);
      setAiChatMessage('');
    }, 2000);
  };

  const handleRegenerateReport = async () => {
    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    try {
      setRegeneratingReport(true);
      setShowRegenerateDialog(false);
      
      const now = new Date();
      const jstDate = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Tokyo' }));
      jstDate.setDate(jstDate.getDate() - 1);
      const year = jstDate.getFullYear();
      const month = String(jstDate.getMonth() + 1).padStart(2, '0');
      const day = String(jstDate.getDate()).padStart(2, '0');
      const reportDate = `${year}-${month}-${day}`;

      const response = await insightsApi.generateDailyInsight({
        agent_type: 'daily_summary',
        prompt: '前日の業務データを基に、新しいDaily Insightsレポートを再生成してください。',
        session_id: sessionId || uuidv4(),
        report_date: reportDate,
      });

      setReportContent(response.response);
      setSessionId(response.session_id);
      setActorId(response.actor_id);
      
      if (!currentInsight) {
        const newInsight = {
          id: response.summary_id,
          user_cd: user.userId,
          str_cd: user.store,
          report_date: reportDate,
          status: 'draft',
          report_text: response.response,
          session_id: response.session_id,
          actor_id: response.actor_id,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        
        setCurrentInsight(newInsight);
      }
    } catch (error) {
      console.error('Failed to regenerate report:', error);
    } finally {
      setRegeneratingReport(false);
    }
  };

  const handleSaveReport = async () => {
    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    try {
      setIsSaving(true);
      
      if (currentInsight) {
        await insightsApi.updateDailyInsight(currentInsight.id, {
          report_date: currentInsight.report_date,
          status: 'completed',
          report_text: reportContent,
          session_id: sessionId,
        });
      }
      
      setShowSaveDialog(false);
      useAppStore.getState().showNotification('Insightsを保存しました', 'success');
      navigate('/');
    } catch (error) {
      console.error('Failed to save report:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleQuickSave = async () => {
    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    try {
      setIsQuickSaving(true);
      
      if (currentInsight) {
        if (currentInsight.status === 'draft') {
          await insightsApi.createDailyInsight(currentInsight.id, {
            report_date: currentInsight.report_date,
            status: 'completed',
            report_text: reportContent,
            session_id: sessionId,
          });
          
          setCurrentInsight({
            ...currentInsight,
            status: 'completed',
            report_text: reportContent,
          });
        } else {
          await insightsApi.updateDailyInsight(currentInsight.id, {
            report_date: currentInsight.report_date,
            status: 'completed',
            report_text: reportContent,
            session_id: sessionId,
          });
        }
        
        useAppStore.getState().showNotification('Insightsを保存しました', 'success');
      } else {
        useAppStore.getState().showNotification('保存するInsightsが見つかりません', 'error');
      }
    } catch (error) {
      console.error('Failed to save report:', error);
      useAppStore.getState().showNotification('保存に失敗しました', 'error');
    } finally {
      setIsQuickSaving(false);
    }
  };

  const handleSaveReaction = async () => {
    try {
      setIsSavingReaction(true);
      
      if (!currentInsight) {
        useAppStore.getState().showNotification('保存するInsightsが見つかりません。先にレポートを保存してください。', 'error');
        return;
      }

      if (!selectedFeedback) {
        useAppStore.getState().showNotification('評価を選択してください。', 'error');
        return;
      }
      
      const feedbackText = selectedFeedback + (userComment ? `: ${userComment}` : '');
      await insightsApi.updateFeedback(currentInsight.id, {
        user_feedback: feedbackText,
      });
      
      setShowReactionSaveDialog(false);
      useAppStore.getState().showNotification('フィードバックを保存しました', 'success');
    } catch (error) {
      console.error('Failed to save feedback:', error);
      useAppStore.getState().showNotification('フィードバックの保存に失敗しました', 'error');
    } finally {
      setIsSavingReaction(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          フィードバック
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {displayDate ? new Date(displayDate).toLocaleDateString('ja-JP') : ''}の内容
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 3 }}>
        <Box sx={{ flex: { xs: 1, lg: 2 }, order: { xs: 1, lg: 1 } }}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">内容</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => setShowRegenerateDialog(true)}
                  disabled={regeneratingReport}
                  size="small"
                >
                  新規作成
                </Button>
                <Box sx={{ position: 'relative' }}>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleQuickSave}
                    size="small"
                    disabled={isQuickSaving}
                  >
                    保存
                  </Button>
                </Box>
              </Box>
            </Box>

            {/* AI Edit Instruction Box */}
            <AiEditInstructionBox
              show={showAiChat}
              message={aiChatMessage}
              onMessageChange={setAiChatMessage}
              onExecuteEdit={handleExecuteAiEdit}
              disabled={processingAiEdit}
            />

            {/* Report Content */}
            {regeneratingReport || processingAiEdit ? (
              <LoadingSpinner 
                message={regeneratingReport ? "日報を再生成しています..." : "AI編集を実行しています..."} 
              />
            ) : (
              <TextField
                fullWidth
                multiline
                rows={25}
                value={reportContent}
                onChange={(e) => setReportContent(e.target.value)}
                sx={{
                  '& .MuiInputBase-input': {
                    fontFamily: 'monospace',
                    fontSize: '0.9rem',
                  },
                }}
              />
            )}

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Box sx={{ position: 'relative' }}>
                <Button
                  variant="contained"
                  color="success"
                  onClick={() => setShowSaveDialog(true)}
                  size="large"
                  disabled={isSaving}
                >
                  完了
                </Button>
                {isSaving && (
                  <CircularProgress
                    size={24}
                    sx={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      marginTop: '-12px',
                      marginLeft: '-12px',
                    }}
                  />
                )}
              </Box>
            </Box>
          </Paper>
        </Box>

        {/* Sidebar */}
        <Box sx={{ flex: { xs: 1, lg: 1 }, order: { xs: 2, lg: 2 } }}>
          {/* AI Feedback */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                フィードバックリアクション
              </Typography>
              
              {!currentInsight && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  フィードバックを保存するには、先にレポートを保存してください。
                </Alert>
              )}
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  評価
                </Typography>
                {['役に立った', '役に立たなかった', '詳しく知りたい', '実施済み', 'その他'].map((option) => (
                  <Button
                    key={option}
                    variant={selectedFeedback === option ? 'contained' : 'outlined'}
                    size="small"
                    onClick={() => setSelectedFeedback(option)}
                    sx={{ mr: 1, mb: 1 }}
                    disabled={!currentInsight}
                  >
                    {option}
                  </Button>
                ))}
              </Box>
              
              {selectedFeedback === 'その他' && (
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder="コメントを入力..."
                  value={userComment}
                  onChange={(e) => setUserComment(e.target.value)}
                  size="small"
                  sx={{ mb: 2 }}
                  disabled={!currentInsight}
                />
              )}
            </CardContent>
            <CardActions>
              <Button
                variant="contained"
                fullWidth
                onClick={() => setShowReactionSaveDialog(true)}
                startIcon={<SaveIcon />}
                disabled={!currentInsight || !selectedFeedback}
              >
                リアクション保存
              </Button>
            </CardActions>
          </Card>

        </Box>
      </Box>

      {/* Save Report Dialog */}
      <ConfirmDialog
        open={showSaveDialog}
        title="内容保存確認"
        message="内容を保存しますか？"
        confirmText="保存"
        cancelText="キャンセル"
        onConfirm={handleSaveReport}
        onCancel={() => setShowSaveDialog(false)}
        loading={isSaving}
      />

      {/* Regenerate Report Dialog */}
      <ConfirmDialog
        open={showRegenerateDialog}
        title="新規作成確認"
        message="Insightsの内容が書き換わり上書き保存されますが新規作成しますか？"
        confirmText="作成"
        cancelText="キャンセル"
        onConfirm={handleRegenerateReport}
        onCancel={() => setShowRegenerateDialog(false)}
      />

      {/* Save Reaction Dialog */}
      <ConfirmDialog
        open={showReactionSaveDialog}
        title="リアクション保存確認"
        message="フィードバックリアクションを保存しますか？"
        confirmText="保存"
        cancelText="キャンセル"
        onConfirm={handleSaveReaction}
        onCancel={() => setShowReactionSaveDialog(false)}
        loading={isSavingReaction}
      />

      <Backdrop
        open={isQuickSaving}
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <CircularProgress color="inherit" size={60} />
          <Typography variant="h6">保存中...</Typography>
        </Box>
      </Backdrop>
    </Container>
  );
};

export default DailyReportPage;