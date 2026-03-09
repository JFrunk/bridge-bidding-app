import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { setUserId, setUserType, clearUserId, trackLogin, trackLogout, trackGuestMode } from '../services/analytics';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Number of hands before prompting for registration
const HANDS_BEFORE_PROMPT = 3;
const HANDS_BEFORE_PROMPT_LEARNING = 5;

// Delay before showing modal after threshold is met (ms)
const PROMPT_DELAY_MS = 3000;

// Generate or retrieve a unique guest ID for this browser
// Uses large negative numbers to avoid collision with real user IDs (which are positive)
const getOrCreateGuestId = () => {
  const GUEST_ID_KEY = 'bridge_guest_id';
  let guestId = localStorage.getItem(GUEST_ID_KEY);

  // Check if we have a valid numeric guest ID
  // Old format was "guest_<timestamp>_<random>" which is invalid
  const numericId = guestId ? parseInt(guestId, 10) : NaN;

  if (!guestId || isNaN(numericId)) {
    // Generate a unique numeric ID using timestamp + random
    // Use numbers in the range -1000000000 to -1 to avoid collision with real IDs
    // Real user IDs start at 1 and increment positively
    const timestamp = Date.now() % 100000000; // Last 8 digits of timestamp
    const random = Math.floor(Math.random() * 100); // 2 random digits
    // Create negative number: e.g., -1735600012345
    const newId = -(timestamp * 100 + random);
    localStorage.setItem(GUEST_ID_KEY, String(newId));
    return newId;
  }

  return numericId;
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [handsCompleted, setHandsCompleted] = useState(0);
  const [bidsPracticed, setBidsPracticed] = useState(0);
  const [skillsPracticed, setSkillsPracticed] = useState(0);
  const [showRegistrationPrompt, setShowRegistrationPrompt] = useState(false);
  const [hasSeenPrompt, setHasSeenPrompt] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    // Check for demo/review mode via URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('demo') === 'true' || urlParams.get('review') === 'true') {
      const guestId = getOrCreateGuestId();
      setUser({ id: guestId, username: 'reviewer', display_name: 'Reviewer', isGuest: true });
      setLoading(false);
      return;
    }

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
      // No stored session - user needs to login or choose guest
      // Setting user to null will trigger login screen
      setUser(null);
      setLoading(false);

      // Clear stale experience level so the Welcome Wizard shows on next login.
      // Without this, a hard reset (backend DB cleared but localStorage persists)
      // would skip the onboarding questionnaire.
      localStorage.removeItem('bridge_experience_level');
    }

    // Load activity counters from localStorage
    const savedHands = localStorage.getItem('bridge_hands_completed');
    if (savedHands) setHandsCompleted(parseInt(savedHands, 10) || 0);
    const savedBids = localStorage.getItem('bridge_bids_practiced');
    if (savedBids) setBidsPracticed(parseInt(savedBids, 10) || 0);
    const savedSkills = localStorage.getItem('bridge_skills_practiced');
    if (savedSkills) setSkillsPracticed(parseInt(savedSkills, 10) || 0);

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
        // Session invalid - require login
        setUser(null);
      }
    } catch (error) {
      console.error('Session validation failed:', error);
      localStorage.removeItem('session_token');
      // Session validation failed - require login
      setUser(null);
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
      // If user is currently a guest, pass their guest_id so backend can migrate their data
      const currentGuestId = user?.isGuest ? user.id : null;

      const response = await fetch(`${API_URL}/api/auth/simple-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [type]: identifier,
          create_if_not_exists: true,
          guest_id: currentGuestId  // Pass guest ID for data migration
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

      // Track login event and set user ID/type for analytics
      setUserId(userData.id);
      setUserType(userData.email);
      trackLogin(type); // 'email' or 'phone'

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
    localStorage.removeItem('bridge_experience_level');

    // Track logout and clear user ID from analytics
    trackLogout();
    clearUserId();

    // Clear user state - this will show login screen (isAuthenticated becomes false)
    setUser(null);
    setLoading(false);
  };

  const continueAsGuest = () => {
    // Each browser gets a unique guest ID to prevent data collision
    const guestId = getOrCreateGuestId();
    const guestUser = { id: guestId, username: 'guest', display_name: 'Guest', isGuest: true };
    setUser(guestUser);
    // Persist to bridge_user so userId survives page refresh.
    // Without this, AuthContext mount finds no stored user → user=null → userId=null
    // → session/start fails, hand saving fails, evaluate-bid fails.
    localStorage.setItem('bridge_user', JSON.stringify(guestUser));

    // Track guest mode and set guest user ID/type for analytics
    setUserId(guestId);
    setUserType(null); // guests are always external
    trackGuestMode();

    setLoading(false);
  };

  // Track activity and mark prompt as ready (shown on next idle moment)
  const promptReadyRef = useRef(false);
  const promptTimerRef = useRef(null);

  // Shared threshold check — triggers prompt when total activity across all modes reaches threshold
  const checkPromptThreshold = useCallback((totalActivity, isLearningMode = false) => {
    const threshold = isLearningMode ? HANDS_BEFORE_PROMPT_LEARNING : HANDS_BEFORE_PROMPT;
    if (totalActivity >= threshold) {
      promptReadyRef.current = true;
      if (promptTimerRef.current) clearTimeout(promptTimerRef.current);
      promptTimerRef.current = setTimeout(() => {
        if (promptReadyRef.current) {
          setShowRegistrationPrompt(true);
          promptReadyRef.current = false;
        }
      }, PROMPT_DELAY_MS);
    }
  }, []);

  const recordHandCompleted = useCallback((isLearningMode = false) => {
    if (user?.isGuest && !hasSeenPrompt) {
      const newCount = handsCompleted + 1;
      setHandsCompleted(newCount);
      localStorage.setItem('bridge_hands_completed', newCount.toString());
      checkPromptThreshold(newCount + bidsPracticed + skillsPracticed, isLearningMode);
    }
  }, [user, handsCompleted, bidsPracticed, skillsPracticed, hasSeenPrompt, checkPromptThreshold]);

  const recordBidCompleted = useCallback(() => {
    if (user?.isGuest && !hasSeenPrompt) {
      const newCount = bidsPracticed + 1;
      setBidsPracticed(newCount);
      localStorage.setItem('bridge_bids_practiced', newCount.toString());
      checkPromptThreshold(handsCompleted + newCount + skillsPracticed);
    }
  }, [user, handsCompleted, bidsPracticed, skillsPracticed, hasSeenPrompt, checkPromptThreshold]);

  const recordSkillPracticed = useCallback(() => {
    if (user?.isGuest && !hasSeenPrompt) {
      const newCount = skillsPracticed + 1;
      setSkillsPracticed(newCount);
      localStorage.setItem('bridge_skills_practiced', newCount.toString());
      checkPromptThreshold(handsCompleted + bidsPracticed + newCount, true);
    }
  }, [user, handsCompleted, bidsPracticed, skillsPracticed, hasSeenPrompt, checkPromptThreshold]);

  // Dismiss registration prompt (temporarily or permanently)
  // "Maybe Later" sets hasSeenPrompt to prevent re-triggering for this session.
  // "Don't Ask Again" additionally persists across sessions via localStorage.
  const dismissRegistrationPrompt = useCallback((permanent = false) => {
    setShowRegistrationPrompt(false);
    setHasSeenPrompt(true);
    promptReadyRef.current = false;
    if (promptTimerRef.current) clearTimeout(promptTimerRef.current);
    if (permanent) {
      localStorage.setItem('bridge_registration_dismissed', 'true');
    }
  }, []);

  // Check if registration is required for a feature
  const requiresRegistration = useCallback((feature) => {
    // Features that require registration
    const protectedFeatures = ['progress', 'dashboard', 'history'];
    return user?.isGuest && protectedFeatures.includes(feature);
  }, [user]);

  // Show deferred prompt immediately (call on navigation/idle moments)
  const showPromptIfReady = useCallback(() => {
    if (promptReadyRef.current && !hasSeenPrompt) {
      if (promptTimerRef.current) clearTimeout(promptTimerRef.current);
      setShowRegistrationPrompt(true);
      promptReadyRef.current = false;
    }
  }, [hasSeenPrompt]);

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
      // Registration prompt — activity tracking
      handsCompleted,
      bidsPracticed,
      skillsPracticed,
      recordHandCompleted,
      recordBidCompleted,
      recordSkillPracticed,
      showRegistrationPrompt,
      dismissRegistrationPrompt,
      requiresRegistration,
      promptForRegistration,
      showPromptIfReady
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
