import React from 'react';
import {
  Box,
  Typography,
  Rating,
  FormControl,
  FormHelperText,
} from '@mui/material';
import { Star, StarBorder } from '@mui/icons-material';

interface RatingQuestionProps {
  question: string;
  value: number | null;
  onChange: (value: number | null) => void;
  required?: boolean;
  error?: boolean;
  helperText?: string;
}

const RatingQuestion: React.FC<RatingQuestionProps> = ({
  question,
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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            不満
          </Typography>
          <Rating
            value={value}
            onChange={(_, newValue) => onChange(newValue)}
            size="large"
            icon={<Star fontSize="inherit" />}
            emptyIcon={<StarBorder fontSize="inherit" />}
            sx={{
              '& .MuiRating-iconFilled': {
                color: '#ff6d75',
              },
              '& .MuiRating-iconHover': {
                color: '#ff3d47',
              },
            }}
          />
          <Typography variant="body2" color="text.secondary">
            満足
          </Typography>
        </Box>
        {helperText && (
          <FormHelperText>{helperText}</FormHelperText>
        )}
      </Box>
    </FormControl>
  );
};

export default RatingQuestion;