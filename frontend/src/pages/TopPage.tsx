import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
} from '@mui/material';
import {
  QuestionAnswer,
  Description,
  History,
} from '@mui/icons-material';

const TopPage: React.FC = () => {
  const navigate = useNavigate();

  console.log('TopPage rendering');

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 4 }}>
        Dashboard
      </Typography>

      <Box 
        sx={{ 
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(3, 1fr)',
          },
          gap: 3,
        }}
      >
        <Card 
          sx={{ 
            height: '100%',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 3,
            },
          }}
          onClick={() => navigate('/daily-answer')}
        >
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <QuestionAnswer 
              sx={{ 
                fontSize: 48, 
                color: 'primary.main',
                mb: 2,
              }} 
            />
            <Typography variant="h6" gutterBottom>
              Daily Survey
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Start today's survey
            </Typography>
          </CardContent>
        </Card>

        <Card 
          sx={{ 
            height: '100%',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 3,
            },
          }}
          onClick={() => navigate('/daily-report')}
        >
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Description 
              sx={{ 
                fontSize: 48, 
                color: 'primary.main',
                mb: 2,
              }} 
            />
            <Typography variant="h6" gutterBottom>
              Daily Insights
            </Typography>
            <Typography variant="body2" color="text.secondary">
              View daily insights
            </Typography>
          </CardContent>
        </Card>

        <Card 
          sx={{ 
            height: '100%',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 3,
            },
          }}
          onClick={() => navigate('/history')}
        >
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <History 
              sx={{ 
                fontSize: 48, 
                color: 'primary.main',
                mb: 2,
              }} 
            />
            <Typography variant="h6" gutterBottom>
              History
            </Typography>
            <Typography variant="body2" color="text.secondary">
              View past records
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default TopPage;