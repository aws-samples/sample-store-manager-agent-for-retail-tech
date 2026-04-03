import React from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
} from '@mui/material';

interface TextQuestionProps {
  question: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  error?: boolean;
  helperText?: string;
  multiline?: boolean;
  rows?: number;
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
}) => {
  return (
    <FormControl fullWidth>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" component="label" sx={{ mb: 2, display: 'block' }}>
          {question}
          {required && <span style={{ color: 'red' }}> *</span>}
        </Typography>
        <TextField
          fullWidth
          multiline={multiline}
          rows={multiline ? rows : 1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          error={error}
          helperText={helperText}
          placeholder="こちらに入力してください..."
          variant="outlined"
        />
      </Box>
    </FormControl>
  );
};

export default TextQuestion;