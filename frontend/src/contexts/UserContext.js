/**
 * User Context - Manages current authenticated user
 *
 * Provides user information throughout the app and handles
 * simple authentication (email/phone based, no passwords for MVP)
 *
 * Also manages experience level for Learning Mode content locking:
 * - experienceLevel: 0 (beginner), 1 (rusty), 99 (expert)
 * - areAllLevelsUnlocked: boolean override to unlock all content
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const UserContext = createContext(null);

// Storage keys
const USER_STORAGE_KEY = 'bridge_current_user';
const EXPERIENCE_STORAGE_KEY = 'bridge_experience_level';

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

  // Experience level state for Learning Mode content locking
  const [experienceLevel, setExperienceLevelState] = useState(null); // null = not set yet (show wizard)
  const [areAllLevelsUnlocked, setAreAllLevelsUnlockedState] = useState(false);

  // Load user and experience from localStorage on mount
  useEffect(() => {
    // Load user
    const storedUser = localStorage.getItem(USER_STORAGE_KEY);
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setCurrentUser(user);
      } catch (e) {
        console.error('Failed to parse stored user:', e);
        localStorage.removeItem(USER_STORAGE_KEY);
      }
    }

    // Load experience level
    const storedExperience = localStorage.getItem(EXPERIENCE_STORAGE_KEY);
    if (storedExperience) {
      try {
        const experience = JSON.parse(storedExperience);
        setExperienceLevelState(experience.level);
        setAreAllLevelsUnlockedState(experience.unlockAll ?? false);
      } catch (e) {
        console.error('Failed to parse stored experience:', e);
        localStorage.removeItem(EXPERIENCE_STORAGE_KEY);
      }
    }

    setLoading(false);
  }, []);

  const login = (user) => {
    setCurrentUser(user);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  };

  const logout = () => {
    setCurrentUser(null);
    localStorage.removeItem(USER_STORAGE_KEY);
    // Note: We keep experience level on logout since it's device-specific preference
  };

  const updateUser = (userData) => {
    const updated = { ...currentUser, ...userData };
    setCurrentUser(updated);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(updated));
  };

  // Set experience level (from WelcomeWizard or Settings)
  const setExperienceLevel = useCallback((data) => {
    const { experienceLevel: level, areAllLevelsUnlocked: unlockAll } = data;
    setExperienceLevelState(level);
    setAreAllLevelsUnlockedState(unlockAll);
    localStorage.setItem(EXPERIENCE_STORAGE_KEY, JSON.stringify({
      level,
      unlockAll,
      experienceId: data.experienceId,
      setAt: new Date().toISOString()
    }));
  }, []);

  // Toggle unlock all levels (from Settings)
  const toggleUnlockAllLevels = useCallback(() => {
    const newUnlockAll = !areAllLevelsUnlocked;
    setAreAllLevelsUnlockedState(newUnlockAll);

    // Update storage
    const storedExperience = localStorage.getItem(EXPERIENCE_STORAGE_KEY);
    if (storedExperience) {
      try {
        const experience = JSON.parse(storedExperience);
        experience.unlockAll = newUnlockAll;
        localStorage.setItem(EXPERIENCE_STORAGE_KEY, JSON.stringify(experience));
      } catch (e) {
        console.error('Failed to update experience:', e);
      }
    }
  }, [areAllLevelsUnlocked]);

  // Check if a level should be unlocked based on experience settings
  // levelNumber: the level_number from the learning status
  // Returns true if the level should be accessible
  const isLevelUnlocked = useCallback((levelNumber) => {
    // If all levels are unlocked, everything is accessible
    if (areAllLevelsUnlocked) return true;

    // If no experience level set, only level 0 is unlocked
    if (experienceLevel === null) return levelNumber === 0;

    // Otherwise, unlock levels up to and including experienceLevel
    return levelNumber <= experienceLevel;
  }, [experienceLevel, areAllLevelsUnlocked]);

  // Check if wizard should be shown (no experience level set yet)
  const shouldShowWelcomeWizard = experienceLevel === null && !loading;

  const value = {
    currentUser,
    loading,
    login,
    logout,
    updateUser,
    isAuthenticated: !!currentUser,
    userId: currentUser?.id || null,
    // Experience level for Learning Mode
    experienceLevel,
    areAllLevelsUnlocked,
    setExperienceLevel,
    toggleUnlockAllLevels,
    isLevelUnlocked,
    shouldShowWelcomeWizard
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};
