import React from 'react';
import './ModeSelector.css';

/**
 * ModeSelector - Landing page component for new and returning users
 *
 * Presents four practice modes with clear descriptions to help users
 * self-select into the appropriate learning path based on their goals.
 */
export function ModeSelector({ onSelectMode, userName, onFeedbackClick }) {
  const modes = [
    {
      id: 'learning',
      icon: '📚',
      title: 'Learning Mode',
      subtitle: 'Structured skill tree with 9 levels and progress tracking',
      description: 'Best for: Filling gaps, mastering specific topics',
      features: [
        'Step-by-step progression from basics to advanced',
        'Practice hands matched to each skill',
        'Track your mastery progress'
      ],
      buttonText: 'Start Learning',
      buttonClass: 'mode-button-learning'
    },
    {
      id: 'freeplay',
      icon: '🎲',
      title: 'Free Practice',
      subtitle: 'Random hands with full auctions and instant feedback',
      description: 'Best for: General practice, realistic scenarios',
      features: [
        'Deal random hands and bid freely',
        'Get feedback on every bid',
        'See how AI would bid differently'
      ],
      buttonText: 'Deal a Hand',
      buttonClass: 'mode-button-freeplay'
    },
    {
      id: 'conventions',
      icon: '🎯',
      title: 'Convention Practice',
      subtitle: 'Curated hands for specific conventions',
      description: 'Best for: Drilling Stayman, Jacoby, Blackwood, etc.',
      features: [
        'Hands designed to trigger specific conventions',
        'Practice until conventions feel automatic',
        'Essential, Intermediate, and Advanced levels'
      ],
      buttonText: 'Choose a Convention',
      buttonClass: 'mode-button-conventions'
    },
    {
      id: 'play',
      icon: '♠',
      title: 'Card Play',
      subtitle: 'Practice card play as declarer or defender',
      description: 'Best for: Improving play technique after bidding',
      features: [
        'AI bids all hands, you focus on play',
        'Practice declarer play strategies',
        'Adjustable AI difficulty (1-10)'
      ],
      buttonText: 'Play a Hand',
      buttonClass: 'mode-button-play'
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
          data-testid="mode-selector-feedback-button"
        >
          📝 Feedback
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
            <div key={mode.id} className="mode-card">
              <div className="mode-card-header">
                <span className="mode-icon">{mode.icon}</span>
                <h3 className="mode-title">{mode.title}</h3>
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
                data-testid={`mode-${mode.id}-button`}
              >
                {mode.buttonText}
              </button>
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <p className="mode-selector-hint">
          You can switch between modes anytime using the navigation menu
        </p>
      </div>
    </div>
  );
}

export default ModeSelector;
