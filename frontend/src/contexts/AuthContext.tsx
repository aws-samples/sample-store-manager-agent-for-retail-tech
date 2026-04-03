import React, { createContext, useContext, useState, useEffect } from 'react';
import { Amplify } from 'aws-amplify';
import { getCurrentUser, fetchUserAttributes, fetchAuthSession, signOut } from 'aws-amplify/auth';
import { Hub } from 'aws-amplify/utils';
import { useAppStore } from '../stores/appStore';
import { localStorage } from '../utils/localStorage';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_APP_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_APP_USER_POOL_CLIENT_ID,
    },
  },
});

interface AuthContextType {
  user: {
    username: string;
    userId: string;
    email: string;
    groups: string[];
  } | null;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<{
    username: string;
    userId: string;
    email: string;
    groups: string[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkUser();
    
    const hubListener = Hub.listen('auth', ({ payload }) => {
      if (payload.event === 'signedIn') {
        checkUser();
      } else if (payload.event === 'signedOut') {
        setUser(null);
      }
    });
    
    return () => hubListener();
  }, []);

  const checkUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      const attributes = await fetchUserAttributes();
      const session = await fetchAuthSession();
      
      if (!currentUser.userId) {
        console.error('Failed to authenticate: userId is required but not found');
        setUser(null);
        setLoading(false);
        return;
      }
      
      const groups = (session.tokens?.idToken?.payload['cognito:groups'] as string[]) || [];
      const primaryGroup = groups.length > 0 ? groups[0] : 'UNKNOWN_STORE';
      
      setUser({
        username: currentUser.username,
        userId: currentUser.userId,
        email: attributes.email || '',
        groups: [primaryGroup],
      });
    } catch (error) {
      console.error('Failed to authenticate user:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      useAppStore.getState().reset();
      localStorage.clearAll();
      await signOut();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
      useAppStore.getState().reset();
      localStorage.clearAll();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
