/**
 * UserMenu - Avatar dropdown menu for user actions
 *
 * UI Redesign v2: Avatar circle with initial, Feedback in dropdown
 */

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useUser } from '../../contexts/UserContext';
import ExperienceSettings from '../settings/ExperienceSettings';
import './UserMenu.css';

const EXPERIENCE_LABELS = {
  0: 'Beginner',
  1: 'Intermediate',
  99: 'Experienced'
};

/**
 * Get user's initial for avatar display
 */
function getUserInitial(user) {
  if (!user) return 'U';
  if (user.isGuest) return 'G';
  if (user.display_name) return user.display_name.charAt(0).toUpperCase();
  if (user.email) return user.email.charAt(0).toUpperCase();
  if (user.phone) return user.phone.charAt(0);
  return 'U';
}

function UserMenu({ onSignInClick, onFeedbackClick }) {
  const { isAuthenticated, user, logout } = useAuth();
  const { experienceLevel, areAllLevelsUnlocked } = useUser();
  const [isOpen, setIsOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close menu on escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  const initial = getUserInitial(user);
  const isGuest = user?.isGuest;

  if (!isAuthenticated) {
    return (
      <button
        onClick={onSignInClick}
        className="user-menu-sign-in-btn"
        data-testid="sign-in-button"
      >
        Sign In
      </button>
    );
  }

  const displayText = user?.email || user?.phone || user?.display_name || 'User';
  const experienceLabel = areAllLevelsUnlocked
    ? 'All Unlocked'
    : EXPERIENCE_LABELS[experienceLevel] || 'Not Set';

  const handleSignOut = () => {
    setIsOpen(false);
    logout();
  };

  const handleOpenSettings = () => {
    setIsOpen(false);
    setShowSettings(true);
  };

  const handleFeedback = () => {
    setIsOpen(false);
    onFeedbackClick?.();
  };

  return (
    <>
      <div className="user-menu-container" ref={menuRef}>
        {/* Avatar circle trigger */}
        <button
          className={`user-menu-avatar-trigger ${isOpen ? 'active' : ''}`}
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
          aria-haspopup="true"
          aria-label="User menu"
          data-testid="user-menu-trigger"
        >
          <span className="user-avatar-circle">{initial}</span>
        </button>

        {isOpen && (
          <div className="user-menu-dropdown" role="menu" data-testid="user-menu-dropdown">
            {/* User Info Header */}
            <div className="user-menu-header">
              <div className="user-avatar-circle user-avatar-large">{initial}</div>
              <div className="user-menu-header-info">
                <span className="user-menu-header-name">
                  {isGuest ? 'Guest User' : displayText}
                </span>
                <span className="user-menu-header-level">
                  Level: {experienceLabel}
                </span>
              </div>
            </div>

            <div className="user-menu-divider" />

            {/* Menu Items */}
            <button
              className="user-menu-item"
              onClick={handleOpenSettings}
              role="menuitem"
              data-testid="user-menu-settings"
            >
              <span className="user-menu-item-label">Settings</span>
            </button>

            <button
              className="user-menu-item"
              onClick={handleFeedback}
              role="menuitem"
              data-testid="user-menu-feedback"
            >
              <span className="user-menu-item-label">Send Feedback</span>
            </button>

            <div className="user-menu-divider" />

            {isGuest ? (
              <>
                <button
                  className="user-menu-item user-menu-item-primary"
                  onClick={() => {
                    setIsOpen(false);
                    onSignInClick?.();
                  }}
                  role="menuitem"
                  data-testid="user-menu-sign-in"
                >
                  <span className="user-menu-item-label">Sign In to Save Progress</span>
                </button>
                <button
                  className="user-menu-item user-menu-item-muted"
                  onClick={handleSignOut}
                  role="menuitem"
                  data-testid="user-menu-logout"
                >
                  <span className="user-menu-item-label">Log Out</span>
                </button>
              </>
            ) : (
              <button
                className="user-menu-item user-menu-item-muted"
                onClick={handleSignOut}
                role="menuitem"
                data-testid="user-menu-logout"
              >
                <span className="user-menu-item-label">Sign Out</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Settings Modal */}
      <ExperienceSettings
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </>
  );
}

export default UserMenu;
