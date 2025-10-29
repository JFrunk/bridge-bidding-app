/**
 * User Context - Manages current authenticated user
 *
 * Provides user information throughout the app and handles
 * simple authentication (email/phone based, no passwords for MVP)
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext(null);

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

export const UserProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('bridge_current_user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setCurrentUser(user);
      } catch (e) {
        console.error('Failed to parse stored user:', e);
        localStorage.removeItem('bridge_current_user');
      }
    }
    setLoading(false);
  }, []);

  const login = (user) => {
    setCurrentUser(user);
    localStorage.setItem('bridge_current_user', JSON.stringify(user));
  };

  const logout = () => {
    setCurrentUser(null);
    localStorage.removeItem('bridge_current_user');
  };

  const updateUser = (userData) => {
    const updated = { ...currentUser, ...userData };
    setCurrentUser(updated);
    localStorage.setItem('bridge_current_user', JSON.stringify(updated));
  };

  const value = {
    currentUser,
    loading,
    login,
    logout,
    updateUser,
    isAuthenticated: !!currentUser,
    userId: currentUser?.id || null
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};
