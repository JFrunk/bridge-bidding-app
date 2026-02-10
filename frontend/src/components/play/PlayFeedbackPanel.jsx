/**
 * PlayFeedbackPanel Component
 *
 * Displays inline feedback after completing a hand of card play.
 * Follows the same pattern as BidFeedbackPanel for consistency.
 *
 * Features:
 * - Shows result (made/down) with color coding
 * - Displays contract, tricks taken, and score
 * - Collapsible score breakdown
 * - Action buttons for next steps
 * - Auto-slides in with animation
 */

import React, { useState, useEffect } from 'react';
import { ScoreBreakdown } from './ScoreBreakdown';
import { BidChip } from '../shared/BidChip';
import { ChevronDown, ChevronUp } from 'lucide-react';
import './PlayFeedbackPanel.css';

// Map result to display config
const RESULT_CONFIG = {
  made: {
    icon: '✓',
    label: 'Made!',
    className: 'feedback-success'
  },
  down: {
    icon: '✗',
    label: 'Down',
    className: 'feedback-failure'
  },
  overtricks: {
    icon: '✓+',
    label: 'Overtricks!',
    className: 'feedback-success'
  }
};

const PlayFeedbackPanel = ({
  scoreData,           // Score data from API
  isVisible,           // Whether to show the panel
  onDismiss,           // Callback when panel is dismissed
  onPlayAnotherHand,   // Play another random hand
  onReplayHand,        // Replay the same hand
  onReviewHand,        // Open hand review page
  onViewProgress,      // Open progress dashboard
  onDealNewHand,       // Deal new hand (restart bidding)
}) => {
  const [isShowing, setIsShowing] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);

  // Handle visibility transitions
  useEffect(() => {
    if (isVisible && scoreData) {
      // Small delay for animation
      const showTimer = setTimeout(() => setIsShowing(true), 50);
      return () => clearTimeout(showTimer);
    } else {
      setIsShowing(false);
    }
  }, [isVisible, scoreData]);

  if (!isVisible || !scoreData) return null;

  const { contract, tricks_taken, tricks_needed, result, score, made, breakdown, overtricks, undertricks } = scoreData;
  const doubledText = contract?.doubled === 2 ? 'XX' : contract?.doubled === 1 ? 'X' : '';

  // Score perspective adjustment (user always plays NS)
  const declarerIsNS = contract?.declarer === 'N' || contract?.declarer === 'S';
  const userScore = declarerIsNS ? score : -score;
  const userMade = declarerIsNS ? made : !made;

  // Determine result type
  const getResultType = () => {
    if (!userMade) return 'down';
    if (overtricks && overtricks > 0) return 'overtricks';
    return 'made';
  };

  const resultType = getResultType();
  const config = RESULT_CONFIG[resultType];

  // Build the contract display string
  const getContractDisplay = () => {
    if (!contract) return '?';
    return `${contract.level}${contract.strain}${doubledText}`;
  };

  // Get result description
  const getResultDescription = () => {
    if (!userMade) {
      const downCount = undertricks || (tricks_needed - tricks_taken);
      return `Down ${downCount}`;
    }
    if (overtricks && overtricks > 0) {
      return `Made +${overtricks}`;
    }
    return 'Made exactly';
  };

  return (
    <div
      className={`play-feedback-panel ${config.className} ${isShowing ? 'showing' : ''}`}
      role="alert"
      aria-live="polite"
      data-testid="play-feedback-panel"
      data-result={resultType}
    >
      {/* Header row with main result */}
      <div className="feedback-header">
        <span className="feedback-icon">{config.icon}</span>
        <span className="feedback-label">{config.label}</span>
        <BidChip bid={getContractDisplay()} />
        <span className="feedback-by">by {contract?.declarer}</span>
        {onDismiss && (
          <button
            className="feedback-dismiss"
            onClick={onDismiss}
            aria-label="Dismiss feedback"
          >
            ×
          </button>
        )}
      </div>

      {/* Result details */}
      <div className="feedback-details">
        <div className="detail-row">
          <span className="detail-label">Tricks:</span>
          <span className="detail-value">{tricks_taken} of {tricks_needed} needed</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Result:</span>
          <span className={`detail-value ${userMade ? 'text-success' : 'text-failure'}`}>
            {getResultDescription()}
          </span>
        </div>
      </div>

      {/* Score display */}
      <div className={`score-display ${userScore >= 0 ? 'score-positive' : 'score-negative'}`}>
        <span className="score-label">Your Score:</span>
        <span className="score-value">
          {userScore >= 0 ? '+' : ''}{userScore}
        </span>
      </div>

      {/* Score breakdown toggle */}
      {breakdown && (
        <button
          className="breakdown-toggle"
          onClick={() => setShowBreakdown(!showBreakdown)}
          aria-expanded={showBreakdown}
        >
          <span>How was this calculated?</span>
          {showBreakdown ? (
            <ChevronUp className="toggle-icon" />
          ) : (
            <ChevronDown className="toggle-icon" />
          )}
        </button>
      )}

      {/* Collapsible breakdown */}
      {showBreakdown && breakdown && (
        <div className="breakdown-container">
          <ScoreBreakdown
            breakdown={breakdown}
            contract={contract}
            made={made}
            overtricks={overtricks || 0}
            undertricks={undertricks || 0}
            tricksNeeded={tricks_needed}
            userPerspective={!declarerIsNS}
          />
        </div>
      )}

      {/* Action buttons */}
      <div className="feedback-actions">
        {onPlayAnotherHand && (
          <button
            className="action-btn action-primary"
            onClick={onPlayAnotherHand}
          >
            Play Another Hand
          </button>
        )}
        <div className="action-row-secondary">
          {onReviewHand && (
            <button
              className="action-btn action-secondary"
              onClick={onReviewHand}
            >
              Review Hand
            </button>
          )}
          {onViewProgress && (
            <button
              className="action-btn action-secondary"
              onClick={onViewProgress}
            >
              My Progress
            </button>
          )}
        </div>
        <div className="action-row-tertiary">
          {onReplayHand && (
            <button
              className="action-btn action-tertiary"
              onClick={onReplayHand}
            >
              Replay Hand
            </button>
          )}
          {onDealNewHand && (
            <button
              className="action-btn action-tertiary"
              onClick={onDealNewHand}
            >
              Bid New Hand
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayFeedbackPanel;
