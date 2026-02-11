/**
 * User Context - Manages current authenticated user and experience level
 *
 * Provides user information throughout the app and handles:
 * - Simple authentication (email/phone based, no passwords for MVP)
 * - Experience level for Learning Mode content locking
 * - Backend sync for persistent experience level storage
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

const UserContext = createContext(null);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';
const EXPERIENCE_STORAGE_KEY = 'bridge_experience_level';
const PREFERENCES_STORAGE_KEY = 'bridge_user_preferences';

// Profile presets - defines default settings for each user segment
// Manual toggles during a session will override these presets
const PROFILE_PRESETS = {
  beginner: {
    biddingCoachEnabled: true,
    playCoachEnabled: true,
    difficulty: 'beginner'  // Maps to AI difficulty 'beginner'
  },
  intermediate: {
    biddingCoachEnabled: true,
    playCoachEnabled: false,
    difficulty: 'intermediate'  // Maps to AI difficulty 'intermediate'
  },
  expert: {
    biddingCoachEnabled: false,
    playCoachEnabled: false,
    difficulty: 'expert'  // Maps to AI difficulty 'expert'
  }
};

// Default to intermediate if segment is undefined
const DEFAULT_SEGMENT = 'intermediate';

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

export const UserProvider = ({ children }) => {
  const { isAuthenticated, isGuest, userId } = useAuth();
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Experience level state
  const [experienceLevel, setExperienceLevelState] = useState(null);
  const [areAllLevelsUnlocked, setAreAllLevelsUnlockedState] = useState(false);
  const [experienceId, setExperienceId] = useState(null);

  // User preferences state (coaches and difficulty)
  // These are initialized from profile presets but can be overridden manually
  const [biddingCoachEnabled, setBiddingCoachEnabled] = useState(true);
  const [playCoachEnabled, setPlayCoachEnabled] = useState(false);
  const [difficulty, setDifficulty] = useState('intermediate');

  // Sync experience level to backend (defined first so it can be used in effects)
  const syncToBackend = useCallback(async (level, unlockAll, expId) => {
    if (!isAuthenticated || isGuest || !userId || userId < 0) {
      return; // Don't sync for guests
    }

    try {
      await fetch(`${API_URL}/api/user/experience-level`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          experience_level: level,
          unlock_all_content: unlockAll,
          experience_id: expId
        })
      });
    } catch (error) {
      console.error('Failed to sync experience level to backend:', error);
      // Local storage still has the value, will sync later
    }
  }, [isAuthenticated, isGuest, userId]);

  // Load user and experience level from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('bridge_current_user');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setCurrentUser(userData);
      } catch (e) {
        console.error('Failed to parse stored user:', e);
        localStorage.removeItem('bridge_current_user');
      }
    }

    // Load experience level from localStorage
    const storedExperience = localStorage.getItem(EXPERIENCE_STORAGE_KEY);
    if (storedExperience) {
      try {
        const expData = JSON.parse(storedExperience);
        setExperienceLevelState(expData.level);
        setAreAllLevelsUnlockedState(expData.unlockAll || false);
        setExperienceId(expData.experienceId || null);
      } catch (e) {
        console.error('Failed to parse stored experience level:', e);
        localStorage.removeItem(EXPERIENCE_STORAGE_KEY);
      }
    }

    // Load user preferences from localStorage
    const storedPrefs = localStorage.getItem(PREFERENCES_STORAGE_KEY);
    if (storedPrefs) {
      try {
        const prefs = JSON.parse(storedPrefs);
        setBiddingCoachEnabled(prefs.biddingCoachEnabled ?? true);
        setPlayCoachEnabled(prefs.playCoachEnabled ?? false);
        setDifficulty(prefs.difficulty ?? 'intermediate');
      } catch (e) {
        console.error('Failed to parse stored preferences:', e);
        localStorage.removeItem(PREFERENCES_STORAGE_KEY);
      }
    }

    setLoading(false);
  }, []);

  // Sync experience level from backend when authenticated user logs in
  useEffect(() => {
    const syncFromBackend = async () => {
      if (!isAuthenticated || isGuest || !userId || userId < 0) {
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/user/experience-level?user_id=${userId}`);
        if (response.ok) {
          const data = await response.json();

          // If backend has experience level set, use it (backend is source of truth)
          if (data.experience_level !== null) {
            setExperienceLevelState(data.experience_level);
            setAreAllLevelsUnlockedState(data.unlock_all_content || false);
            setExperienceId(data.experience_id);

            // Update localStorage to match backend
            localStorage.setItem(EXPERIENCE_STORAGE_KEY, JSON.stringify({
              level: data.experience_level,
              unlockAll: data.unlock_all_content || false,
              experienceId: data.experience_id,
              setAt: data.experience_set_at
            }));
          } else {
            // Backend has no experience level - check if we have local setting to push up
            const storedExperience = localStorage.getItem(EXPERIENCE_STORAGE_KEY);
            if (storedExperience) {
              const localData = JSON.parse(storedExperience);
              // Push local settings to backend
              await syncToBackend(localData.level, localData.unlockAll, localData.experienceId);
            }
          }
        }
      } catch (error) {
        console.error('Failed to sync experience level from backend:', error);
        // Continue with localStorage values
      }
    };

    syncFromBackend();
  }, [isAuthenticated, isGuest, userId, syncToBackend]);

  // Set experience level (from WelcomeWizard or Settings)
  const setExperienceLevel = useCallback((data) => {
    const { experienceLevel: level, areAllLevelsUnlocked: unlockAll, experienceId: expId } = data;

    setExperienceLevelState(level);
    setAreAllLevelsUnlockedState(unlockAll);
    setExperienceId(expId);

    // Save to localStorage
    localStorage.setItem(EXPERIENCE_STORAGE_KEY, JSON.stringify({
      level,
      unlockAll,
      experienceId: expId,
      setAt: new Date().toISOString()
    }));

    // Sync to backend (async, non-blocking)
    syncToBackend(level, unlockAll, expId);
  }, [syncToBackend]);

  // Toggle unlock all levels
  const toggleUnlockAllLevels = useCallback(() => {
    const newUnlockAll = !areAllLevelsUnlocked;
    setAreAllLevelsUnlockedState(newUnlockAll);

    // Update localStorage
    const storedExperience = localStorage.getItem(EXPERIENCE_STORAGE_KEY);
    const current = storedExperience ? JSON.parse(storedExperience) : { level: experienceLevel, experienceId };

    localStorage.setItem(EXPERIENCE_STORAGE_KEY, JSON.stringify({
      ...current,
      unlockAll: newUnlockAll,
      setAt: new Date().toISOString()
    }));

    // Sync to backend
    syncToBackend(current.level, newUnlockAll, current.experienceId);
  }, [areAllLevelsUnlocked, experienceLevel, experienceId, syncToBackend]);

  // Update user preferences (persists to localStorage)
  const updatePreferences = useCallback((newPrefs) => {
    if (newPrefs.biddingCoachEnabled !== undefined) {
      setBiddingCoachEnabled(newPrefs.biddingCoachEnabled);
    }
    if (newPrefs.playCoachEnabled !== undefined) {
      setPlayCoachEnabled(newPrefs.playCoachEnabled);
    }
    if (newPrefs.difficulty !== undefined) {
      setDifficulty(newPrefs.difficulty);
    }

    // Save to localStorage
    const storedPrefs = localStorage.getItem(PREFERENCES_STORAGE_KEY);
    const currentPrefs = storedPrefs ? JSON.parse(storedPrefs) : {};
    const updatedPrefs = { ...currentPrefs, ...newPrefs, setAt: new Date().toISOString() };
    localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(updatedPrefs));
  }, []);

  // Apply profile presets (used when user selects a profile in WelcomeWizard)
  const applyProfilePresets = useCallback((profileId) => {
    const presets = PROFILE_PRESETS[profileId] || PROFILE_PRESETS[DEFAULT_SEGMENT];
    setBiddingCoachEnabled(presets.biddingCoachEnabled);
    setPlayCoachEnabled(presets.playCoachEnabled);
    setDifficulty(presets.difficulty);

    // Save to localStorage
    localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify({
      ...presets,
      appliedFromProfile: profileId,
      setAt: new Date().toISOString()
    }));

    return presets;
  }, []);

  // Get current profile presets for a segment (without applying)
  const getProfilePresets = useCallback((profileId) => {
    return PROFILE_PRESETS[profileId] || PROFILE_PRESETS[DEFAULT_SEGMENT];
  }, []);

  // Check if a level should be unlocked based on experience
  const isLevelUnlocked = useCallback((levelNumber) => {
    // Unlock all override
    if (areAllLevelsUnlocked) return true;

    // No experience set - only level 0 is unlocked
    if (experienceLevel === null) return levelNumber === 0;

    // Level is within user's experience range
    return levelNumber <= experienceLevel;
  }, [experienceLevel, areAllLevelsUnlocked]);

  // Should show welcome wizard (first-time user, no experience level set)
  const shouldShowWelcomeWizard = experienceLevel === null && !loading;

  const login = (userData) => {
    setCurrentUser(userData);
    localStorage.setItem('bridge_current_user', JSON.stringify(userData));
  };

  const logout = () => {
    setCurrentUser(null);
    localStorage.removeItem('bridge_current_user');
    // Note: We keep experience level on logout (device-specific, not account-specific)
  };

  const updateUser = (userData) => {
    const updated = { ...currentUser, ...userData };
    setCurrentUser(updated);
    localStorage.setItem('bridge_current_user', JSON.stringify(updated));
  };

  const value = {
    // User state
    currentUser,
    loading,
    login,
    logout,
    updateUser,
    isAuthenticated: !!currentUser || isAuthenticated,
    userId: currentUser?.id || userId || null,

    // Experience level state
    experienceLevel,
    areAllLevelsUnlocked,
    experienceId,
    setExperienceLevel,
    toggleUnlockAllLevels,
    isLevelUnlocked,
    shouldShowWelcomeWizard,

    // User preferences (coaches and difficulty)
    biddingCoachEnabled,
    playCoachEnabled,
    difficulty,
    updatePreferences,
    applyProfilePresets,
    getProfilePresets
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};
