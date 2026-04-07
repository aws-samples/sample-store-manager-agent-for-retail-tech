import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import { useVoiceInput } from '../../hooks/useVoiceInput';

interface TextQuestionProps {
  question: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  error?: boolean;
  helperText?: string;
  multiline?: boolean;
  rows?: number;
  enableVoiceInput?: boolean;
}

const TextQuestion: React.FC<TextQuestionProps> = ({
  question,
  value,
  onChange,
  required = false,
  error = false,
  helperText,
  multiline = true,
  rows = 4,
  enableVoiceInput = true,
}) => {
  const [displayText, setDisplayText] = useState('');
  // 録音開始時点のテキストを保持
  const baseTextRef = useRef('');

  const {
    isRecording,
    state,
    error: voiceError,
    startRecording,
    stopRecording,
  } = useVoiceInput({
    onInterimResult: (text) => {
      // フックから累積テキストが来る（確定分 + 中間分）
      const fullText = baseTextRef.current 
        ? `${baseTextRef.current} ${text}` 
        : text;
      setDisplayText(fullText);
    },
    onFinalResult: (text) => {
      // フックから累積された確定テキストが来る
      const fullText = baseTextRef.current 
        ? `${baseTextRef.current} ${text}` 
        : text;
      setDisplayText(fullText);
      onChange(fullText);
    },
    onError: (err) => {
      console.error('Voice input error:', err);
    },
  });

  const handleMicClick = async () => {
    if (isRecording) {
      await stopRecording();
      // 停止後、displayTextがあればそれを保存
      if (displayText) {
        onChange(displayText);
      }
    } else {
      // 録音開始時に現在のvalueをベースとして保持
      baseTextRef.current = value;
      setDisplayText(value);
      await startRecording();
    }
  };

  // 録音中はdisplayText、それ以外はvalue
  const shownValue = isRecording ? displayText : value;

  return (
    <FormControl fullWidth>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" component="label" sx={{ mb: 2, display: 'block' }}>
          {question}
          {required && <span style={{ color: 'red' }}> *</span>}
        </Typography>
        <Box sx={{ position: 'relative' }}>
          <TextField
            fullWidth
            multiline={multiline}
            rows={multiline ? rows : 1}
            value={shownValue}
            onChange={(e) => onChange(e.target.value)}
            error={error || !!voiceError}
            helperText={voiceError || helperText}
            placeholder="こちらに入力してください..."
            variant="outlined"
            InputProps={{
              sx: isRecording ? { 
                backgroundColor: 'rgba(244, 67, 54, 0.05)',
                borderColor: 'error.main',
              } : {},
            }}
          />
          {enableVoiceInput && (
            <Tooltip title={isRecording ? '録音停止' : '音声入力'}>
              <IconButton
                onClick={handleMicClick}
                disabled={state === 'processing'}
                sx={{
                  position: 'absolute',
                  right: 8,
                  bottom: 8,
                  color: isRecording ? 'error.main' : 'primary.main',
                  backgroundColor: isRecording ? 'error.light' : 'transparent',
                  '&:hover': {
                    backgroundColor: isRecording ? 'error.light' : 'action.hover',
                  },
                }}
              >
                {state === 'processing' ? (
                  <CircularProgress size={24} />
                ) : isRecording ? (
                  <MicOffIcon />
                ) : (
                  <MicIcon />
                )}
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>
    </FormControl>
  );
};

export default TextQuestion;
