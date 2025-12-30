import React, { useState, useEffect } from 'react';
import './AIDifficultySelector.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Get session ID from localStorage (same as api.js SessionManager)
const getSessionId = () => {
  return localStorage.getItem('bridge_session_id') || 'default';
};

// Base difficulty info - expert rating/description updated dynamically based on DDS availability
const DIFFICULTY_INFO = {
  beginner: {
    name: 'Beginner',
    rating: '6/10',
    description: 'Basic rule-based play',
    emoji: '🌱',
    color: '#4caf50'
  },
  intermediate: {
    name: 'Intermediate',
    rating: '7.5/10',
    description: 'Enhanced evaluation with strategic thinking',
    emoji: '📚',
    color: '#2196f3'
  },
  advanced: {
    name: 'Advanced',
    rating: '8/10',
    description: 'Deep analysis with tactical awareness',
    emoji: '🎯',
    color: '#ff9800'
  },
  expert: {
    name: 'Expert',
    rating: '9/10',
    description: 'Double Dummy Solver - perfect play',
    emoji: '🏆',
    color: '#f44336'
  }
};

const AIDifficultySelector = ({ onDifficultyChange }) => {
  const [currentDifficulty, setCurrentDifficulty] = useState(null); // Start as null until fetched from backend
  const [isChanging, setIsChanging] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [ddsStatus, setDdsStatus] = useState({
    ddsActive: false,
    isProduction: false,
    platform: 'unknown',
    ddsDisabledReason: null
  });

  useEffect(() => {
    // Fetch current difficulty on mount
    fetchCurrentDifficulty();
  }, []);

  const fetchCurrentDifficulty = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_URL}/api/ai/status`, {
        headers: { 'X-Session-ID': getSessionId() }
      });
      if (response.ok) {
        const data = await response.json();
        const backendDifficulty = data.current_difficulty;
        console.log('✅ Fetched current AI difficulty from backend:', backendDifficulty);
        console.log('   DDS Active:', data.dds_active, '| Platform:', data.platform, '| Environment:', data.environment);
        setCurrentDifficulty(backendDifficulty || 'intermediate');

        // Track DDS status for display
        setDdsStatus({
          ddsActive: data.dds_active || false,
          isProduction: data.is_production || false,
          platform: data.platform || 'unknown',
          environment: data.environment || 'development',
          ddsDisabledReason: data.dds_disabled_reason
        });
      } else {
        console.error('Failed to fetch AI difficulty, defaulting to intermediate');
        setCurrentDifficulty('intermediate');
      }
    } catch (error) {
      console.error('Failed to fetch current difficulty:', error);
      setCurrentDifficulty('intermediate'); // Fallback to intermediate on error
    } finally {
      setIsLoading(false);
    }
  };

  const handleDifficultyChange = async (newDifficulty) => {
    if (newDifficulty === currentDifficulty || isChanging) return;

    setIsChanging(true);
    try {
      const response = await fetch(`${API_URL}/api/set-ai-difficulty`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': getSessionId()
        },
        body: JSON.stringify({ difficulty: newDifficulty })
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentDifficulty(newDifficulty);

        // Auto-close dropdown after selection
        setShowInfo(false);

        if (onDifficultyChange) {
          onDifficultyChange(newDifficulty, data);
        }
      } else {
        console.error('Failed to set difficulty');
      }
    } catch (error) {
      console.error('Error setting difficulty:', error);
    } finally {
      setIsChanging(false);
    }
  };

  // Show loading state until we fetch actual difficulty from backend
  if (isLoading || !currentDifficulty) {
    return (
      <div className="ai-difficulty-selector">
        <div className="difficulty-header">
          <span className="difficulty-label">AI Difficulty:</span>
          <button className="difficulty-current" disabled>
            <span className="difficulty-emoji">⋯</span>
            <span className="difficulty-name">Loading...</span>
          </button>
        </div>
      </div>
    );
  }

  // Get difficulty info, adjusting expert based on DDS availability
  const getDifficultyInfo = (key) => {
    const info = { ...DIFFICULTY_INFO[key] };
    if (key === 'expert' && !ddsStatus.ddsActive) {
      // DDS not active - show fallback info
      info.rating = '8+/10';
      info.description = 'Deep minimax search (4-ply)';
    }
    return info;
  };

  const currentInfo = getDifficultyInfo(currentDifficulty);

  return (
    <div className="ai-difficulty-selector">
      <div className="difficulty-header">
        <span className="difficulty-label">AI Difficulty:</span>
        <button
          className="difficulty-current"
          onClick={() => setShowInfo(!showInfo)}
          style={{ borderColor: currentInfo.color }}
        >
          <span className="difficulty-emoji">{currentInfo.emoji}</span>
          <span className="difficulty-name">{currentInfo.name}</span>
          <span className="difficulty-rating">{currentInfo.rating}</span>
          <span className="expand-arrow">{showInfo ? '▼' : '▶'}</span>
        </button>
      </div>

      {showInfo && (
        <div className="difficulty-options">
          {/* DDS Status Banner */}
          <div className={`dds-status-banner ${ddsStatus.ddsActive ? 'dds-active' : 'dds-inactive'}`}>
            <span className="dds-status-icon">{ddsStatus.ddsActive ? '✅' : '⚠️'}</span>
            <span className="dds-status-text">
              {ddsStatus.ddsActive
                ? 'DDS Active (Production)'
                : `DDS Disabled (${ddsStatus.platform})`}
            </span>
            {!ddsStatus.ddsActive && ddsStatus.ddsDisabledReason && (
              <span className="dds-reason">{ddsStatus.ddsDisabledReason}</span>
            )}
          </div>

          {Object.entries(DIFFICULTY_INFO).map(([key, baseInfo]) => {
            const info = getDifficultyInfo(key);
            const isActive = key === currentDifficulty;
            const isExpertWithoutDDS = key === 'expert' && !ddsStatus.ddsActive;
            return (
              <button
                key={key}
                className={`difficulty-option ${isActive ? 'active' : ''} ${isChanging ? 'disabled' : ''}`}
                onClick={() => handleDifficultyChange(key)}
                disabled={isChanging || isActive}
                style={{
                  borderLeftColor: info.color,
                  backgroundColor: isActive ? `${info.color}15` : 'white'
                }}
              >
                <div className="option-header">
                  <span className="option-emoji">{info.emoji}</span>
                  <span className="option-name">{info.name}</span>
                  <span className="option-rating">{info.rating}</span>
                  {isExpertWithoutDDS && <span className="fallback-badge">Fallback</span>}
                  {isActive && <span className="active-indicator">✓</span>}
                </div>
                <div className="option-description">{info.description}</div>
              </button>
            );
          })}

          <div className="difficulty-note">
            <strong>Note:</strong> Expert difficulty uses DDS (Double Dummy Solver) for perfect play
            {ddsStatus.ddsActive
              ? ' - currently active in production.'
              : ` - currently using Minimax fallback on ${ddsStatus.platform}.`}
            {' '}Change difficulty before starting a new hand.
          </div>
        </div>
      )}
    </div>
  );
};

export default AIDifficultySelector;
