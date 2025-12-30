import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Number of hands before prompting for registration
const HANDS_BEFORE_PROMPT = 3;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [handsCompleted, setHandsCompleted] = useState(0);
  const [showRegistrationPrompt, setShowRegistrationPrompt] = useState(false);
  const [hasSeenPrompt, setHasSeenPrompt] = useState(false);

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
      // Auto-continue as guest for frictionless first experience
      const guestUser = { id: 1, username: 'guest', display_name: 'Guest', isGuest: true };
      setUser(guestUser);
      setLoading(false);
    }

    // Load hands completed from localStorage
    const savedHands = localStorage.getItem('bridge_hands_completed');
    if (savedHands) {
      setHandsCompleted(parseInt(savedHands, 10) || 0);
    }

    // Check if user has already dismissed the prompt
    const dismissed = localStorage.getItem('bridge_registration_dismissed');
    if (dismissed) {
      setHasSeenPrompt(true);
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
        // Auto-continue as guest
        const guestUser = { id: 1, username: 'guest', display_name: 'Guest', isGuest: true };
        setUser(guestUser);
      }
    } catch (error) {
      console.error('Session validation failed:', error);
      localStorage.removeItem('session_token');
      // Auto-continue as guest
      const guestUser = { id: 1, username: 'guest', display_name: 'Guest', isGuest: true };
      setUser(guestUser);
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
      // Hide the registration prompt
      setShowRegistrationPrompt(false);

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
    // Keep them as guest after logout
    const guestUser = { id: 1, username: 'guest', display_name: 'Guest', isGuest: true };
    setUser(guestUser);
  };

  const continueAsGuest = () => {
    // Use existing guest functionality with user_id = 1 (default guest)
    setUser({ id: 1, username: 'guest', display_name: 'Guest', isGuest: true });
    setLoading(false);
  };

  // Track completed hands and trigger registration prompt
  const recordHandCompleted = useCallback(() => {
    if (user?.isGuest && !hasSeenPrompt) {
      const newCount = handsCompleted + 1;
      setHandsCompleted(newCount);
      localStorage.setItem('bridge_hands_completed', newCount.toString());

      // Show registration prompt after threshold
      if (newCount >= HANDS_BEFORE_PROMPT) {
        setShowRegistrationPrompt(true);
      }
    }
  }, [user, handsCompleted, hasSeenPrompt]);

  // Dismiss registration prompt (temporarily or permanently)
  const dismissRegistrationPrompt = useCallback((permanent = false) => {
    setShowRegistrationPrompt(false);
    if (permanent) {
      setHasSeenPrompt(true);
      localStorage.setItem('bridge_registration_dismissed', 'true');
    }
  }, []);

  // Check if registration is required for a feature
  const requiresRegistration = useCallback((feature) => {
    // Features that require registration
    const protectedFeatures = ['progress', 'dashboard', 'history'];
    return user?.isGuest && protectedFeatures.includes(feature);
  }, [user]);

  // Trigger registration prompt for protected features
  const promptForRegistration = useCallback(() => {
    if (user?.isGuest) {
      setShowRegistrationPrompt(true);
      return true;
    }
    return false;
  }, [user]);

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
      userId: user?.id || null,
      // New registration prompt features
      handsCompleted,
      recordHandCompleted,
      showRegistrationPrompt,
      dismissRegistrationPrompt,
      requiresRegistration,
      promptForRegistration
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
