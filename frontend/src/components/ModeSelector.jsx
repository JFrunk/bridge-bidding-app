import React from 'react';
import PropTypes from 'prop-types';
import './ModeSelector.css';

/**
 * ModeSelector - Landing page component for new and returning users
 *
 * Presents four practice modes with clear descriptions to help users
 * self-select into the appropriate learning path based on their goals.
 *
 * Modes:
 * - Learn: Structured curriculum with skill tree
 * - Bid: Practice bidding (Random, Conventions, History sub-modes)
 * - Play: Practice card play
 * - Progress: View stats and learning insights
 */
export function ModeSelector({ onSelectMode, userName, onFeedbackClick }) {
  const modes = [
    {
      id: 'learning',
      icon: '📚',
      title: 'Learn',
      subtitle: 'Structured lessons from basics to advanced',
      description: 'Best for: Building solid foundations, filling knowledge gaps',
      features: [
        'Step-by-step skill progression (9 levels)',
        'Practice hands matched to each topic',
        'Track your mastery progress'
      ],
      buttonText: 'Start Learning',
      buttonClass: 'mode-button-learning'
    },
    {
      id: 'bid',
      icon: '🎲',
      title: 'Bid',
      subtitle: 'Practice bidding with random hands or conventions',
      description: 'Best for: General practice, drilling specific conventions',
      features: [
        'Random hands for realistic practice',
        'Convention drills organized by level',
        'Replay hands from this session'
      ],
      buttonText: 'Start Bidding',
      buttonClass: 'mode-button-bid'
    },
    {
      id: 'play',
      icon: '♠',
      title: 'Play',
      subtitle: 'Practice card play as declarer or defender',
      description: 'Best for: Improving play technique',
      features: [
        'New hands with AI bidding',
        'Play the hand you just bid',
        'Replay previous hands'
      ],
      buttonText: 'Start Playing',
      buttonClass: 'mode-button-play'
    },
    {
      id: 'progress',
      icon: '📊',
      title: 'Progress',
      subtitle: 'View your stats and learning insights',
      description: 'Best for: Tracking improvement, identifying areas to work on',
      features: [
        'Bidding quality statistics',
        'Recent decisions with feedback',
        'Personalized recommendations'
      ],
      buttonText: 'View Progress',
      buttonClass: 'mode-button-progress'
    }
  ];

  return (
    <div className="mode-selector-container">
      {/* Global Feedback Button - Always visible */}
      {onFeedbackClick && (
        <button
          className="mode-selector-feedback-button"
          onClick={onFeedbackClick}
          title="Report an issue or give feedback"
          aria-label="Report an issue or give feedback"
          data-testid="mode-selector-feedback-button"
        >
          <span aria-hidden="true">📝</span> Feedback
        </button>
      )}

      <div className="mode-selector-content">
        {/* Header */}
        <div className="mode-selector-header">
          <h1 className="mode-selector-title">
            Bridge Bidding Trainer
          </h1>
          <p className="mode-selector-subtitle">
            Learn Standard American Yellow Card (SAYC) bidding through interactive practice
          </p>
          {userName && (
            <p className="mode-selector-welcome">
              Welcome back, {userName}
            </p>
          )}
        </div>

        {/* Mode Selection Prompt */}
        <div className="mode-selector-prompt">
          <h2>Choose Your Practice Mode</h2>
        </div>

        {/* Mode Cards Grid */}
        <div className="mode-cards-grid">
          {modes.map((mode) => (
            <div key={mode.id} className="mode-card" role="article" aria-labelledby={`mode-title-${mode.id}`}>
              <div className="mode-card-header">
                <span className="mode-icon" aria-hidden="true">{mode.icon}</span>
                <h3 className="mode-title" id={`mode-title-${mode.id}`}>{mode.title}</h3>
              </div>

              <p className="mode-subtitle">{mode.subtitle}</p>

              <ul className="mode-features">
                {mode.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>

              <p className="mode-description">{mode.description}</p>

              <button
                className={`mode-button ${mode.buttonClass}`}
                onClick={() => onSelectMode(mode.id)}
                aria-describedby={`mode-title-${mode.id}`}
                data-testid={`mode-${mode.id}-button`}
              >
                {mode.buttonText}
              </button>
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <p className="mode-selector-hint">
          You can switch between modes anytime using the 🏠 button
        </p>
      </div>
    </div>
  );
}

ModeSelector.propTypes = {
  onSelectMode: PropTypes.func.isRequired,
  userName: PropTypes.string,
  onFeedbackClick: PropTypes.func
};

ModeSelector.defaultProps = {
  userName: null,
  onFeedbackClick: null
};

export default ModeSelector;
