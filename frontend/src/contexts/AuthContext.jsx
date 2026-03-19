import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { setUserId, setUserType, clearUserId, trackLogin, trackLogout, trackGuestMode } from '../services/analytics';
import * as authApi from '../services/authApi';
import { setAccessTokenGetter } from '../utils/sessionHelper';

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

  // V2 Auth: JWT access token lives in memory only (not localStorage)
  const accessTokenRef = useRef(null);
  const refreshTimerRef = useRef(null);

  // Register token getter so sessionHelper can include JWT in API headers
  useEffect(() => {
    setAccessTokenGetter(() => accessTokenRef.current);
  }, []);

  // ─── V2 Auth Helpers ──────────────────────────────────────

  /**
   * Store access token in memory and set user from V2 auth response.
   * V2 responses always include { access_token, user_id }.
   */
  const handleAuthSuccess = useCallback((data, extra = {}) => {
    accessTokenRef.current = data.access_token;

    const userData = {
      id: data.user_id,
      email: extra.email || '',
      display_name: extra.display_name || '',
      isGuest: false,
      emailVerified: extra.email_verified ?? data.email_verified ?? false,
      authVersion: 'v2',
    };

    setUser(userData);
    // Store minimal user info for page reload recovery
    // (access token will be recovered via refresh cookie)
    localStorage.setItem('bridge_user', JSON.stringify(userData));
    setShowRegistrationPrompt(false);

    // Analytics
    setUserId(userData.id);
    setUserType(userData.email);

    // Schedule token refresh (refresh 1 minute before 15-min expiry)
    scheduleTokenRefresh();
  }, []);

  /**
   * Try to restore session via refresh token cookie on page load.
   * PRD §3.1: access token is memory-only, so every page load
   * must call /api/auth/refresh to get a new one.
   */
  const tryRefreshSession = useCallback(async () => {
    try {
      const result = await authApi.refreshAccessToken();
      if (result.success) {
        accessTokenRef.current = result.data.access_token;
        // Restore user from stored data, update ID from refresh response
        const storedUser = localStorage.getItem('bridge_user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          userData.id = result.data.user_id;
          setUser(userData);
          localStorage.setItem('bridge_user', JSON.stringify(userData));
        } else {
          setUser({
            id: result.data.user_id,
            isGuest: false,
            authVersion: 'v2',
          });
        }
        scheduleTokenRefresh();
        return true;
      }
    } catch (e) {
      // Refresh failed — user needs to log in again
    }
    return false;
  }, []);

  const scheduleTokenRefresh = useCallback(() => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    // Refresh 1 minute before 15-min expiry = 14 minutes
    refreshTimerRef.current = setTimeout(async () => {
      const result = await authApi.refreshAccessToken();
      if (result.success) {
        accessTokenRef.current = result.data.access_token;
        scheduleTokenRefresh();
      }
    }, 14 * 60 * 1000);
  }, []);

  // ─── Initialization ───────────────────────────────────────

  useEffect(() => {
    const init = async () => {
      // Check for demo/review mode via URL parameter
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('demo') === 'true' || urlParams.get('review') === 'true') {
        const guestId = getOrCreateGuestId();
        setUser({ id: guestId, username: 'reviewer', display_name: 'Reviewer', isGuest: true });
        setLoading(false);
        return;
      }

      // Check stored user — determine if V2 or legacy
      const storedUser = localStorage.getItem('bridge_user');
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);

          if (userData.authVersion === 'v2') {
            // V2 user: try to restore session via refresh cookie
            const refreshed = await tryRefreshSession();
            if (!refreshed) {
              // Refresh failed — clear stale data, require login
              localStorage.removeItem('bridge_user');
              setUser(null);
            }
            setLoading(false);
            return;
          }

          // Legacy user (simple auth or guest): restore directly
          setUser(userData);
          setLoading(false);
          return;
        } catch (e) {
          console.error('Failed to parse stored user:', e);
          localStorage.removeItem('bridge_user');
        }
      }

      // Fall back to legacy token-based validation
      const token = localStorage.getItem('session_token');
      if (token) {
        validateSession(token);
        return;
      }

      // No stored session — user needs to login or choose guest
      setUser(null);
      setLoading(false);
      localStorage.removeItem('bridge_experience_level');

      // Load activity counters from localStorage
      const savedHands = localStorage.getItem('bridge_hands_completed');
      if (savedHands) setHandsCompleted(parseInt(savedHands, 10) || 0);
      const savedBids = localStorage.getItem('bridge_bids_practiced');
      if (savedBids) setBidsPracticed(parseInt(savedBids, 10) || 0);
      const savedSkills = localStorage.getItem('bridge_skills_practiced');
      if (savedSkills) setSkillsPracticed(parseInt(savedSkills, 10) || 0);

      const dismissed = localStorage.getItem('bridge_registration_dismissed');
      if (dismissed) setHasSeenPrompt(true);
    };

    init();

    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Legacy Auth Methods (kept for backward compatibility) ─

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
        setUser(null);
      }
    } catch (error) {
      console.error('Session validation failed:', error);
      localStorage.removeItem('session_token');
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
      const currentGuestId = user?.isGuest ? user.id : null;

      const response = await fetch(`${API_URL}/api/auth/simple-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [type]: identifier,
          create_if_not_exists: true,
          guest_id: currentGuestId
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Login failed');
      }

      const data = await response.json();

      const userData = {
        id: data.user_id,
        email: data.email,
        phone: data.phone,
        display_name: data.email || data.phone,
        isGuest: false
      };

      setUser(userData);
      localStorage.setItem('bridge_user', JSON.stringify(userData));
      setShowRegistrationPrompt(false);

      setUserId(userData.id);
      setUserType(userData.email);
      trackLogin(type);

      return { success: true, created: data.created, user: userData };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  // ─── V2 Auth Methods ──────────────────────────────────────

  const registerV2 = useCallback(async ({ email, password, displayName }) => {
    const guestId = user?.isGuest ? user.id : null;
    const result = await authApi.registerUser({ email, password, displayName, guestId });

    if (result.success) {
      handleAuthSuccess(result.data, {
        email,
        display_name: displayName,
        email_verified: false,
      });
      trackLogin('register');
      return { success: true, isNewUser: true };
    }

    return { success: false, error: result.error };
  }, [user, handleAuthSuccess]);

  const loginV2 = useCallback(async ({ email, password }) => {
    const result = await authApi.loginUser({ email, password });

    if (result.success) {
      handleAuthSuccess(result.data, { email });
      trackLogin('password');
      return { success: true };
    }

    return { success: false, error: result.error, status: result.status };
  }, [handleAuthSuccess]);

  const loginWithGoogle = useCallback(async (idToken) => {
    const guestId = user?.isGuest ? user.id : null;
    const result = await authApi.googleAuth({ idToken, guestId });

    if (result.success) {
      handleAuthSuccess(result.data, { email_verified: true });
      trackLogin('google');
      return { success: true, isNewUser: result.data.is_new_user };
    }

    return { success: false, error: result.error, status: result.status };
  }, [user, handleAuthSuccess]);

  const requestMagicLink = useCallback(async (email) => {
    return authApi.requestMagicLink(email);
  }, []);

  const verifyMagicLink = useCallback(async (token) => {
    const result = await authApi.verifyMagicLink(token);

    if (result.success) {
      handleAuthSuccess(result.data, { email_verified: true });
      trackLogin('magic_link');
      return { success: true };
    }

    return { success: false, error: result.error };
  }, [handleAuthSuccess]);

  const resendVerification = useCallback(async () => {
    if (!user?.email) return { success: false, error: 'No email' };
    return authApi.resendVerification(user.email);
  }, [user]);

  // ─── Logout ───────────────────────────────────────────────

  const logout = async () => {
    // V2 logout: revoke refresh token cookie
    if (accessTokenRef.current) {
      try {
        await authApi.logoutV2();
      } catch (e) {
        // Best effort
      }
      accessTokenRef.current = null;
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    }

    // Legacy logout
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

    trackLogout();
    clearUserId();

    setUser(null);
    setLoading(false);
  };

  // ─── Guest Mode ───────────────────────────────────────────

  const continueAsGuest = () => {
    const guestId = getOrCreateGuestId();
    const guestUser = { id: guestId, username: 'guest', display_name: 'Guest', isGuest: true };
    setUser(guestUser);
    localStorage.setItem('bridge_user', JSON.stringify(guestUser));

    setUserId(guestId);
    setUserType(null);
    trackGuestMode();

    setLoading(false);
  };

  // ─── Registration Prompt (guest activity tracking) ────────

  const promptReadyRef = useRef(false);
  const promptTimerRef = useRef(null);

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

  const dismissRegistrationPrompt = useCallback((permanent = false) => {
    setShowRegistrationPrompt(false);
    setHasSeenPrompt(true);
    promptReadyRef.current = false;
    if (promptTimerRef.current) clearTimeout(promptTimerRef.current);
    if (permanent) {
      localStorage.setItem('bridge_registration_dismissed', 'true');
    }
  }, []);

  const requiresRegistration = useCallback((feature) => {
    const protectedFeatures = ['progress', 'dashboard', 'history'];
    return user?.isGuest && protectedFeatures.includes(feature);
  }, [user]);

  const showPromptIfReady = useCallback(() => {
    if (promptReadyRef.current && !hasSeenPrompt) {
      if (promptTimerRef.current) clearTimeout(promptTimerRef.current);
      setShowRegistrationPrompt(true);
      promptReadyRef.current = false;
    }
  }, [hasSeenPrompt]);

  const promptForRegistration = useCallback(() => {
    if (user?.isGuest) {
      setShowRegistrationPrompt(true);
      return true;
    }
    return false;
  }, [user]);

  const getAuthToken = () => {
    // V2: return in-memory JWT
    if (accessTokenRef.current) return accessTokenRef.current;
    // Legacy: return stored session token
    return localStorage.getItem('session_token');
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      isAuthenticated: user !== null,
      isGuest: user?.isGuest || false,
      userId: user?.id || null,

      // V2 Auth
      registerV2,
      loginV2,
      loginWithGoogle,
      requestMagicLink,
      verifyMagicLink,
      resendVerification,
      getAccessToken: () => accessTokenRef.current,

      // Legacy (kept for backward compatibility)
      login,
      simpleLogin,
      getAuthToken,

      // Shared
      logout,
      continueAsGuest,

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
