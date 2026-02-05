/**
 * UserMenu - Dropdown menu for user actions and settings
 *
 * Provides access to:
 * - User display name/email
 * - Settings (Experience Level)
 * - Sign In / Sign Out
 */

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useUser } from '../../contexts/UserContext';
import ExperienceSettings from '../settings/ExperienceSettings';
import './UserMenu.css';

const EXPERIENCE_LABELS = {
  0: 'Beginner',
  1: 'Rusty',
  99: 'Experienced'
};

function UserMenu({ onSignInClick }) {
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
  const isGuest = user?.isGuest;
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

  return (
    <>
      <div className="user-menu-container" ref={menuRef}>
        <button
          className={`user-menu-trigger ${isOpen ? 'active' : ''}`}
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
          aria-haspopup="true"
          data-testid="user-menu-trigger"
        >
          <span className="user-menu-avatar">👤</span>
          <span className="user-menu-name">
            {isGuest ? 'Guest' : displayText}
          </span>
          <span className={`user-menu-chevron ${isOpen ? 'open' : ''}`}>▼</span>
        </button>

        {isOpen && (
          <div className="user-menu-dropdown" role="menu" data-testid="user-menu-dropdown">
            {/* User Info Header */}
            <div className="user-menu-header">
              <div className="user-menu-header-avatar">👤</div>
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
              <span className="user-menu-item-icon">⚙️</span>
              <span className="user-menu-item-label">Settings</span>
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
                  <span className="user-menu-item-icon">🔑</span>
                  <span className="user-menu-item-label">Sign In to Save Progress</span>
                </button>
                <button
                  className="user-menu-item user-menu-item-danger"
                  onClick={handleSignOut}
                  role="menuitem"
                  data-testid="user-menu-logout"
                >
                  <span className="user-menu-item-icon">🚪</span>
                  <span className="user-menu-item-label">Log Out</span>
                </button>
              </>
            ) : (
              <button
                className="user-menu-item user-menu-item-danger"
                onClick={handleSignOut}
                role="menuitem"
                data-testid="user-menu-logout"
              >
                <span className="user-menu-item-icon">🚪</span>
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
