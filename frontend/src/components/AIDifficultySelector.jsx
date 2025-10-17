import React, { useState, useEffect } from 'react';
import './AIDifficultySelector.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

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
  const [currentDifficulty, setCurrentDifficulty] = useState('intermediate'); // Default to stable level
  const [isChanging, setIsChanging] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    // Fetch current difficulty on mount
    fetchCurrentDifficulty();
  }, []);

  const fetchCurrentDifficulty = async () => {
    try {
      const response = await fetch(`${API_URL}/api/ai/status`);
      if (response.ok) {
        const data = await response.json();
        setCurrentDifficulty(data.current_difficulty || 'intermediate');
      }
    } catch (error) {
      console.error('Failed to fetch current difficulty:', error);
    }
  };

  const handleDifficultyChange = async (newDifficulty) => {
    if (newDifficulty === currentDifficulty || isChanging) return;

    setIsChanging(true);
    try {
      const response = await fetch(`${API_URL}/api/set-ai-difficulty`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  const currentInfo = DIFFICULTY_INFO[currentDifficulty];

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
          {Object.entries(DIFFICULTY_INFO).map(([key, info]) => {
            const isActive = key === currentDifficulty;
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
                  {isActive && <span className="active-indicator">✓</span>}
                </div>
                <div className="option-description">{info.description}</div>
              </button>
            );
          })}

          <div className="difficulty-note">
            <strong>Note:</strong> Expert difficulty uses DDS (Double Dummy Solver) for near-perfect play when available.
            This provides the best AI performance but may be unstable on some systems.
            Change difficulty before starting a new hand.
          </div>
        </div>
      )}
    </div>
  );
};

export default AIDifficultySelector;
