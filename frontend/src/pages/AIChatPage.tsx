import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Send as SendIcon, SmartToy as AIIcon, Person as PersonIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/appStore';
import { chatApi } from '../services/chatApi';
import VoiceTextField from '../components/common/VoiceTextField';
import type { ChatMessage } from '../types';

const AIChatPage: React.FC = () => {
  const navigate = useNavigate();
  const { getChatSession, setChatSession, loading, setLoading, user } = useAppStore();
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatSession = getChatSession();

  useEffect(() => {
    if (!chatSession) {
      navigate('/daily-answer');
      return;
    }
    setChatMessages(chatSession.messages);
  }, [chatSession, navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSendMessage = async () => {
    if (!message.trim() || isTyping || !chatSession) return;

    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    const userMessage: ChatMessage = {
      role: 'user',
      content: message.trim(),
      timestamp: new Date(),
    };

    const updatedMessages = [...chatMessages, userMessage];
    setChatMessages(updatedMessages);
    setMessage('');
    setIsTyping(true);

    try {
      const response = await chatApi.sendMessage({
        agent_type: 'hearing',
        prompt: message.trim(),
        session_id: chatSession.session_id,
        survey_id: chatSession.survey_id,
      });

      const aiMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };

      const finalMessages = [...updatedMessages, aiMessage];
      setChatMessages(finalMessages);
      
      setChatSession({
        ...chatSession,
        messages: finalMessages,
      });
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleGoToConfirm = async () => {
    if (!chatSession) return;

    if (!user) {
      console.error('User not authenticated');
      navigate('/');
      return;
    }

    try {
      setLoading(true);
      await chatApi.saveSession({
        survey_id: chatSession.survey_id,
        session_id: chatSession.session_id,
      });
      navigate('/answer-confirm');
    } catch (error) {
      console.error('Failed to save session:', error);
    } finally {
      setLoading(false);
    }
  };



  return (
    <Container maxWidth="md" sx={{ py: 4, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ヘッダー */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            AIチャット
          </Typography>
          <Typography variant="body2" color="text.secondary">
            今日の業務について詳しくお聞かせください
          </Typography>
        </Box>
        
        {/* 確認画面へボタン（右上に配置） */}
        <Button
          variant="contained"
          onClick={handleGoToConfirm}
          disabled={loading || chatMessages.length <= 1}
          sx={{ minWidth: 120 }}
        >
          {loading ? <CircularProgress size={20} /> : '確認画面へ'}
        </Button>
      </Box>

      {/* チャット履歴エリア */}
      <Paper 
        elevation={1} 
        sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden',
          mb: 2,
        }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AIIcon color="primary" />
            AI アシスタント
          </Typography>
        </Box>
        
        <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
          <List sx={{ py: 0 }}>
            {chatMessages.slice(1).map((msg, index) => (
              <ListItem
                key={index}
                sx={{
                  display: 'flex',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-start',
                  gap: 1,
                  mb: 2,
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: msg.role === 'user' ? 'primary.main' : 'secondary.main',
                    width: 32,
                    height: 32,
                  }}
                >
                  {msg.role === 'user' ? <PersonIcon /> : <AIIcon />}
                </Avatar>
                
                <Box
                  sx={{
                    maxWidth: '70%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.100',
                      color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                      borderRadius: 2,
                      borderTopLeftRadius: msg.role === 'user' ? 2 : 0.5,
                      borderTopRightRadius: msg.role === 'user' ? 0.5 : 2,
                    }}
                  >
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </Typography>
                  </Paper>
                </Box>
              </ListItem>
            ))}
            
            {/* AIタイピング中の表示 */}
            {isTyping && (
              <ListItem sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                  <AIIcon />
                </Avatar>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label="入力中..."
                    size="small"
                    icon={<CircularProgress size={12} />}
                    sx={{ bgcolor: 'grey.100' }}
                  />
                </Box>
              </ListItem>
            )}
          </List>
          <div ref={messagesEndRef} />
        </Box>
      </Paper>

      {/* メッセージ入力エリア */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <VoiceTextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="メッセージを入力してください..."
            value={message}
            onChange={(val) => setMessage(val)}
            onKeyDown={handleKeyDown}
            disabled={isTyping}
            variant="outlined"
            size="small"
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={!message.trim() || isTyping}
            sx={{ minWidth: 'auto', p: 1.5 }}
            aria-label="send"
          >
            <SendIcon />
          </Button>
        </Box>
      </Paper>


    </Container>
  );
};

export default AIChatPage;