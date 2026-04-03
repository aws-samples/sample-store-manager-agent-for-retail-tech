import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Box,
  Typography,
  Divider,
  Avatar,
  useMediaQuery,
  useTheme,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Assignment as AssignmentIcon,
  Description as DescriptionIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../../stores/appStore';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar: React.FC = () => {
  const theme = useTheme();
  const isNarrow = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarCollapsed, setSidebarCollapsed, user } = useAppStore();
  const { logout } = useAuth();

  React.useEffect(() => {
    if (isNarrow && !sidebarCollapsed) {
      setSidebarCollapsed(true);
    }
  }, [isNarrow, sidebarCollapsed, setSidebarCollapsed]);

  const sidebarWidth = sidebarCollapsed ? 64 : 240;

  const handleSignOut = async () => {
    await logout();
    navigate('/');
  };

  const isAdmin = user?.store === 'admin';

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: <HomeIcon /> },
    { path: '/daily-answer', label: 'Daily Survey', icon: <AssignmentIcon /> },
    { path: '/daily-report', label: 'Daily Insights', icon: <DescriptionIcon /> },
    { path: '/history', label: 'History', icon: <HistoryIcon /> },
    ...(isAdmin ? [{ path: '/admin', label: 'Admin', icon: <SettingsIcon /> }] : []),
  ];

  const handleToggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: sidebarCollapsed ? 'center' : 'space-between',
          minHeight: 64,
        }}
      >
        {!sidebarCollapsed && (
          <Typography variant="body1" noWrap sx={{ color: 'primary.main', fontWeight: 'bold', fontSize: '0.9rem' }}>
            Store Manager Agent
          </Typography>
        )}
        <IconButton onClick={handleToggleSidebar} size="small">
          <MenuIcon />
        </IconButton>
      </Box>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ flexGrow: 1, px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => handleNavigate(item.path)}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'white',
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                },
                '&:hover': {
                  backgroundColor: sidebarCollapsed ? 'action.hover' : 'primary.light',
                  color: sidebarCollapsed ? 'inherit' : 'white',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: sidebarCollapsed ? 'auto' : 40,
                  justifyContent: 'center',
                }}
              >
                {item.icon}
              </ListItemIcon>
              {!sidebarCollapsed && <ListItemText primary={item.label} />}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      {/* User Info */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
          }}
        >
          <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
            <PersonIcon fontSize="small" />
          </Avatar>
          {!sidebarCollapsed && (
            <Box sx={{ ml: 1 }}>
              <Typography variant="body2" fontWeight="bold">
                {user?.email ? user.email.split('@')[0] : 'Guest'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {user?.store || 'N/A'}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                {user?.userId || 'N/A'}
              </Typography>
            </Box>
          )}
        </Box>
        {!sidebarCollapsed && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<LogoutIcon />}
            onClick={handleSignOut}
            fullWidth
          >
            Sign Out
          </Button>
        )}
        {sidebarCollapsed && (
          <IconButton onClick={handleSignOut} size="small">
            <LogoutIcon />
          </IconButton>
        )}
      </Box>
    </Box>
  );

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: sidebarWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: sidebarWidth,
          boxSizing: 'border-box',
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          overflowX: 'hidden',
          zIndex: theme.zIndex.drawer,
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
};

export default Sidebar;