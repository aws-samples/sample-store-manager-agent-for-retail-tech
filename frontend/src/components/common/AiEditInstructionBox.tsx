import React from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Collapse,
} from '@mui/material';
import {
  Send as SendIcon,
} from '@mui/icons-material';

interface AiEditInstructionBoxProps {
  show: boolean;
  message: string;
  onMessageChange: (message: string) => void;
  onExecuteEdit: () => void;
  disabled?: boolean;
}

const AiEditInstructionBox: React.FC<AiEditInstructionBoxProps> = ({
  show,
  message,
  onMessageChange,
  onExecuteEdit,
  disabled = false,
}) => {
  return (
    <Collapse in={show}>
      <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="subtitle2" sx={{ mb: 2 }}>
          AI編集指示
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="修正指示を入力してください..."
            value={message}
            onChange={(e) => onMessageChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (message.trim() && !disabled) {
                  onExecuteEdit();
                }
              }
            }}
          />
          <Button
            variant="outlined"
            size="small"
            startIcon={<SendIcon />}
            onClick={onExecuteEdit}
            disabled={!message.trim() || disabled}
          >
            AI編集実行
          </Button>
        </Box>
      </Box>
    </Collapse>
  );
};

export default AiEditInstructionBox;