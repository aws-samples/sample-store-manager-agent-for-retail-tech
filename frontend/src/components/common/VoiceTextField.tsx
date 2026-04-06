/**
 * VoiceTextField - 音声入力対応テキストフィールド
 * 
 * MUIのTextFieldにマイクボタンを追加したコンポーネント
 */

import React, { useState, useRef } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import type { TextFieldProps } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import { useVoiceInput } from '../../hooks/useVoiceInput';

interface VoiceTextFieldProps extends Omit<TextFieldProps, 'value' | 'onChange'> {
  value: string;
  onChange: (value: string) => void;
  enableVoiceInput?: boolean;
}

const VoiceTextField: React.FC<VoiceTextFieldProps> = ({
  value,
  onChange,
  enableVoiceInput = true,
  disabled,
  ...textFieldProps
}) => {
  const [displayText, setDisplayText] = useState('');
  const baseTextRef = useRef('');
  const prevValueRef = useRef(value);

  // 外部からvalueがクリアされた場合、内部状態もリセット
  React.useEffect(() => {
    if (prevValueRef.current !== '' && value === '') {
      // valueが空にクリアされた
      baseTextRef.current = '';
      setDisplayText('');
    }
    prevValueRef.current = value;
  }, [value]);

  const {
    isRecording,
    state,
    error: voiceError,
    startRecording,
    stopRecording,
  } = useVoiceInput({
    onInterimResult: (text) => {
      const fullText = baseTextRef.current 
        ? `${baseTextRef.current} ${text}` 
        : text;
      setDisplayText(fullText);
    },
    onFinalResult: (text) => {
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
      if (displayText) {
        onChange(displayText);
      }
    } else {
      baseTextRef.current = value;
      setDisplayText(value);
      await startRecording();
    }
  };

  const shownValue = isRecording ? displayText : value;

  return (
    <Box sx={{ position: 'relative', width: '100%' }}>
      <TextField
        {...textFieldProps}
        value={shownValue}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        error={textFieldProps.error || !!voiceError}
        helperText={voiceError || textFieldProps.helperText}
        InputProps={{
          ...textFieldProps.InputProps,
          sx: {
            ...(textFieldProps.InputProps?.sx || {}),
            ...(isRecording ? { 
              backgroundColor: 'rgba(244, 67, 54, 0.05)',
            } : {}),
            pr: enableVoiceInput ? 6 : undefined,
          },
        }}
      />
      {enableVoiceInput && (
        <Tooltip title={isRecording ? '録音停止' : '音声入力'}>
          <IconButton
            onClick={handleMicClick}
            disabled={disabled || state === 'processing'}
            sx={{
              position: 'absolute',
              right: 8,
              top: '50%',
              transform: 'translateY(-50%)',
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
  );
};

export default VoiceTextField;
