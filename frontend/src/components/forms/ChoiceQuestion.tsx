import React from 'react';
import {
  Box,
  Typography,
  FormControl,
  FormControlLabel,
  RadioGroup,
  Radio,
  FormHelperText,
} from '@mui/material';

interface ChoiceQuestionProps {
  question: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  error?: boolean;
  helperText?: string;
}

const ChoiceQuestion: React.FC<ChoiceQuestionProps> = ({
  question,
  options,
  value,
  onChange,
  required = false,
  error = false,
  helperText,
}) => {
  return (
    <FormControl fullWidth error={error}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" component="label" sx={{ mb: 2, display: 'block' }}>
          {question}
          {required && <span style={{ color: 'red' }}> *</span>}
        </Typography>
        <RadioGroup
          value={value}
          onChange={(e) => onChange(e.target.value)}
          sx={{ ml: 2 }}
        >
          {options.map((option, index) => (
            <FormControlLabel
              key={index}
              value={option}
              control={<Radio />}
              label={option}
              sx={{ mb: 1 }}
            />
          ))}
        </RadioGroup>
        {helperText && (
          <FormHelperText>{helperText}</FormHelperText>
        )}
      </Box>
    </FormControl>
  );
};

export default ChoiceQuestion;