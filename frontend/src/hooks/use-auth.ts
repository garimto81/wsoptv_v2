'use client';

import { useState, useEffect } from 'react';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
  status: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

/**
 * Authentication hook
 * Manages auth state from localStorage
 */
export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  useEffect(() => {
    // Check localStorage for auth data
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user') || localStorage.getItem('auth_user');

    if (token && userData) {
      try {
        const user = JSON.parse(userData);
        setState({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch {
        // Invalid data, clear and set as unauthenticated
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('auth_user');
        setState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    } else {
      setState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  }, []);

  return state;
}

export default useAuth;
