import React from 'react';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { useAppStore } from '../../stores/appStore';
import Sidebar from './Sidebar';

const AppLayout: React.FC = () => {
  const theme = useTheme();
  const isNarrow = useMediaQuery(theme.breakpoints.down('md'));
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore();

  React.useEffect(() => {
    if (isNarrow && !sidebarCollapsed) {
      setSidebarCollapsed(true);
    }
  }, [isNarrow, sidebarCollapsed, setSidebarCollapsed]);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          backgroundColor: '#f5f5f5',
          minHeight: '100vh',
          overflow: 'hidden',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default AppLayout;