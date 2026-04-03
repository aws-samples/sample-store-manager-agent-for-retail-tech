import React from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
} from '@mui/material';

interface NumberQuestionProps {
  question: string;
  value: string | number;
  onChange: (value: string) => void;
  required?: boolean;
  error?: boolean;
  helperText?: string;
}

const NumberQuestion: React.FC<NumberQuestionProps> = ({
  question,
  value,
  onChange,
  required = false,
  error = false,
  helperText,
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
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          error={error}
          helperText={helperText}
          placeholder="数値を入力してください..."
          variant="outlined"
        />
      </Box>
    </FormControl>
  );
};

export default NumberQuestion;
