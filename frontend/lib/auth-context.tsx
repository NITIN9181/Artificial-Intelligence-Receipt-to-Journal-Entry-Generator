"use client";

import { createContext, useContext, ReactNode } from 'react';
import { User } from '@/types';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from './api-client';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isReviewer: boolean;
  isPreparer: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data: user, isLoading } = useQuery({
    queryKey: ['user'],
    queryFn: () => apiClient<User>('/auth/me'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  });

  return (
    <AuthContext.Provider
      value={{
        user: user || null,
        isLoading,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'ADMIN',
        isReviewer: user?.role === 'REVIEWER' || user?.role === 'ADMIN',
        isPreparer: user?.role === 'PREPARER' || user?.role === 'REVIEWER' || user?.role === 'ADMIN',
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
