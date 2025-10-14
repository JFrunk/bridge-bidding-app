/**
 * Celebration Notification Component
 *
 * Shows celebration notifications as animated toasts when achievements are unlocked.
 * Can be displayed inline or as a modal overlay.
 */

import React, { useState, useEffect } from 'react';
import './CelebrationNotification.css';

const CelebrationNotification = ({
  celebration,
  onClose,
  autoClose = true,
  autoCloseDelay = 5000,
  variant = 'toast' // 'toast' or 'modal'
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    setTimeout(() => setIsVisible(true), 10);

    // Auto-close if enabled
    if (autoClose && autoCloseDelay > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, autoCloseDelay);

      return () => clearTimeout(timer);
    }
  }, [autoClose, autoCloseDelay]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      setIsVisible(false);
      if (onClose) {
        onClose();
      }
    }, 300); // Match exit animation duration
  };

  if (!celebration) {
    return null;
  }

  if (variant === 'modal') {
    return (
      <CelebrationModal
        celebration={celebration}
        isVisible={isVisible}
        isExiting={isExiting}
        onClose={handleClose}
      />
    );
  }

  return (
    <CelebrationToast
      celebration={celebration}
      isVisible={isVisible}
      isExiting={isExiting}
      onClose={handleClose}
    />
  );
};

// Toast variant (bottom-right corner)
const CelebrationToast = ({ celebration, isVisible, isExiting, onClose }) => {
  return (
    <div
      className={`celebration-toast ${isVisible ? 'visible' : ''} ${isExiting ? 'exiting' : ''}`}
    >
      <div className="celebration-toast-content">
        <div className="celebration-toast-emoji">{celebration.emoji || '🎉'}</div>
        <div className="celebration-toast-body">
          <h4 className="celebration-toast-title">{celebration.title}</h4>
          <p className="celebration-toast-message">{celebration.message}</p>
          {celebration.xp_reward > 0 && (
            <div className="celebration-toast-xp">+{celebration.xp_reward} XP</div>
          )}
        </div>
        <button className="celebration-toast-close" onClick={onClose}>
          ×
        </button>
      </div>
    </div>
  );
};

// Modal variant (center of screen with overlay)
const CelebrationModal = ({ celebration, isVisible, isExiting, onClose }) => {
  return (
    <div
      className={`celebration-modal-overlay ${isVisible ? 'visible' : ''} ${isExiting ? 'exiting' : ''}`}
      onClick={onClose}
    >
      <div
        className="celebration-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <button className="celebration-modal-close" onClick={onClose}>
          ×
        </button>

        <div className="celebration-modal-emoji-large">
          {celebration.emoji || '🎉'}
        </div>

        <h2 className="celebration-modal-title">{celebration.title}</h2>

        <p className="celebration-modal-message">{celebration.message}</p>

        {celebration.xp_reward > 0 && (
          <div className="celebration-modal-xp">
            <span className="xp-label">XP Earned</span>
            <span className="xp-value">+{celebration.xp_reward}</span>
          </div>
        )}

        <button className="celebration-modal-button" onClick={onClose}>
          Awesome!
        </button>
      </div>
    </div>
  );
};

// Container for multiple toast notifications
export const CelebrationToastContainer = ({ celebrations, onClose }) => {
  const [visibleCelebrations, setVisibleCelebrations] = useState([]);

  useEffect(() => {
    if (celebrations && celebrations.length > 0) {
      setVisibleCelebrations(celebrations);
    }
  }, [celebrations]);

  const handleCloseCelebration = (celebrationId) => {
    setVisibleCelebrations((prev) =>
      prev.filter((c) => c.id !== celebrationId)
    );
    if (onClose) {
      onClose(celebrationId);
    }
  };

  return (
    <div className="celebration-toast-container">
      {visibleCelebrations.map((celebration, index) => (
        <CelebrationNotification
          key={celebration.id || index}
          celebration={celebration}
          onClose={() => handleCloseCelebration(celebration.id)}
          variant="toast"
          autoClose={true}
          autoCloseDelay={6000}
        />
      ))}
    </div>
  );
};

export default CelebrationNotification;
