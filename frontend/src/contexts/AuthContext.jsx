import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    // First check for simple auth user (no token required)
    const storedUser = localStorage.getItem('bridge_user');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
        setLoading(false);
        return;
      } catch (e) {
        console.error('Failed to parse stored user:', e);
        localStorage.removeItem('bridge_user');
      }
    }

    // Fall back to token-based validation
    const token = localStorage.getItem('session_token');
    if (token) {
      validateSession(token);
    } else {
      setLoading(false);
    }
  }, []);

  const validateSession = async (token) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/session`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        localStorage.removeItem('session_token');
      }
    } catch (error) {
      console.error('Session validation failed:', error);
      localStorage.removeItem('session_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Login failed');
      }

      const data = await response.json();

      // Store session token
      localStorage.setItem('session_token', data.session_token);
      setUser(data.user);

      return { success: true, isNewUser: data.is_new_user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  // Simple login using email/phone (no password)
  const simpleLogin = async (identifier, type = 'email') => {
    try {
      const response = await fetch(`${API_URL}/api/auth/simple-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [type]: identifier,
          create_if_not_exists: true
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Login failed');
      }

      const data = await response.json();

      // Set user with ID from database
      const userData = {
        id: data.user_id,
        email: data.email,
        phone: data.phone,
        display_name: data.email || data.phone,
        isGuest: false
      };

      setUser(userData);
      // Store user data for persistence
      localStorage.setItem('bridge_user', JSON.stringify(userData));

      return { success: true, created: data.created, user: userData };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    const token = localStorage.getItem('session_token');

    if (token) {
      try {
        await fetch(`${API_URL}/api/auth/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    localStorage.removeItem('session_token');
    localStorage.removeItem('bridge_user');
    setUser(null);
  };

  const continueAsGuest = () => {
    // Use existing guest functionality with user_id = 1 (default guest)
    setUser({ id: 1, username: 'guest', display_name: 'Guest', isGuest: true });
    setLoading(false);
  };

  const getAuthToken = () => {
    return localStorage.getItem('session_token');
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      simpleLogin,
      logout,
      continueAsGuest,
      loading,
      isAuthenticated: user !== null,
      isGuest: user?.isGuest || false,
      getAuthToken,
      userId: user?.id || null
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
