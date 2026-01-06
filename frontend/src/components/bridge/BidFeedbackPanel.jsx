/**
 * BidFeedbackPanel Component
 *
 * Displays real-time feedback after each user bid.
 * Auto-links bridge terms to the glossary for educational value.
 *
 * Features:
 * - Shows correctness rating (optimal, acceptable, suboptimal, error)
 * - Displays optimal bid if user's was incorrect
 * - Links convention/concept terms to glossary
 * - Auto-dismisses after a configurable time or on next bid
 * - Optional differential analysis expansion for detailed "Why?" view
 */

import React, { useState, useEffect } from 'react';
import { TermHighlight } from '../glossary/TermTooltip';
import DifferentialAnalysisPanel from '../learning/DifferentialAnalysisPanel';
import './BidFeedbackPanel.css';

// Map correctness levels to display info
const CORRECTNESS_CONFIG = {
  optimal: {
    icon: '✓',
    label: 'Excellent!',
    className: 'feedback-optimal'
  },
  acceptable: {
    icon: '✓',
    label: 'Good',
    className: 'feedback-acceptable'
  },
  suboptimal: {
    icon: '△',
    label: 'Consider',
    className: 'feedback-suboptimal'
  },
  error: {
    icon: '✗',
    label: 'Better bid:',
    className: 'feedback-error'
  }
};

const BidFeedbackPanel = ({
  feedback,           // Feedback object from API { correctness, score, optimal_bid, reasoning, key_concept, helpful_hint, impact, ... }
  userBid,            // The bid the user made
  isVisible,          // Whether to show the panel
  onDismiss,          // Callback when panel is dismissed
  onOpenGlossary,     // Callback to open glossary drawer with a term
  autoDismissMs = 0,  // Auto-dismiss after N milliseconds (0 = never)
  mode = 'review',    // 'review' (post-move) or 'consultant' (pre-move preview)
  // New props for differential analysis
  differentialData = null,  // Pre-loaded differential data from evaluate-bid response
  handCards = null,   // Hand cards for fetching differential analysis
  auctionHistory = [], // Auction history for fetching differential analysis
  position = 'S',
  vulnerability = 'None',
  dealer = 'N',
}) => {
  const [isShowing, setIsShowing] = useState(false);
  const [showDifferential, setShowDifferential] = useState(false);

  // Handle visibility transitions
  useEffect(() => {
    if (isVisible && feedback) {
      // Small delay for animation
      const showTimer = setTimeout(() => setIsShowing(true), 50);
      return () => clearTimeout(showTimer);
    } else {
      setIsShowing(false);
    }
  }, [isVisible, feedback]);

  // Auto-dismiss functionality
  useEffect(() => {
    if (isShowing && autoDismissMs > 0) {
      const dismissTimer = setTimeout(() => {
        setIsShowing(false);
        if (onDismiss) onDismiss();
      }, autoDismissMs);
      return () => clearTimeout(dismissTimer);
    }
  }, [isShowing, autoDismissMs, onDismiss]);

  if (!isVisible || !feedback) return null;

  const correctnessLevel = feedback.correctness || 'optimal';
  const config = CORRECTNESS_CONFIG[correctnessLevel] || CORRECTNESS_CONFIG.optimal;
  const isCorrect = correctnessLevel === 'optimal' || correctnessLevel === 'acceptable';

  // Build the message content
  const getMessage = () => {
    if (correctnessLevel === 'optimal') {
      return (
        <>
          <span className="feedback-icon">{config.icon}</span>
          <span className="feedback-label">{config.label}</span>
          <span className="feedback-bid">{userBid}</span>
          <span className="feedback-text">is perfect here.</span>
        </>
      );
    }

    if (correctnessLevel === 'acceptable') {
      return (
        <>
          <span className="feedback-icon">{config.icon}</span>
          <span className="feedback-bid">{userBid}</span>
          <span className="feedback-text">is acceptable.</span>
          {feedback.optimal_bid && feedback.optimal_bid !== userBid && (
            <span className="feedback-optimal-note">
              (Optimal: <strong>{feedback.optimal_bid}</strong>)
            </span>
          )}
        </>
      );
    }

    // Suboptimal or error
    return (
      <>
        <span className="feedback-icon">{config.icon}</span>
        <span className="feedback-label">{config.label}</span>
        <span className="feedback-optimal-bid">{feedback.optimal_bid}</span>
        {correctnessLevel === 'suboptimal' && (
          <span className="feedback-text">would be better than {userBid}.</span>
        )}
      </>
    );
  };

  // Get the explanation/hint with term highlighting
  const getExplanation = () => {
    // Priority: helpful_hint > reasoning
    const text = feedback.helpful_hint || feedback.reasoning || '';
    if (!text) return null;

    return (
      <div className="feedback-explanation">
        <TermHighlight text={text} onOpenGlossary={onOpenGlossary} />
      </div>
    );
  };

  // Get the concept/convention link
  const getConcept = () => {
    const concept = feedback.key_concept;
    if (!concept) return null;

    return (
      <div className="feedback-concept">
        <span className="concept-label">Concept:</span>
        <TermHighlight text={concept} onOpenGlossary={onOpenGlossary} />
      </div>
    );
  };

  // Determine if this is a Governor-level warning (critical impact)
  const isGovernorWarning = feedback.impact === 'critical' || feedback.impact === 'significant';
  const isConsultantMode = mode === 'consultant';

  return (
    <div
      className={`bid-feedback-panel ${config.className} ${isShowing ? 'showing' : ''} ${isConsultantMode ? 'consultant-mode' : ''} ${isGovernorWarning ? 'governor-block' : ''}`}
      role="alert"
      aria-live="polite"
      data-testid="bid-feedback-panel"
      data-correctness={correctnessLevel}
      data-mode={mode}
    >
      {/* Consultant Mode indicator */}
      {isConsultantMode && (
        <div className="consultant-tag" data-testid="consultant-tag">
          🔮 AI Consultant Preview
        </div>
      )}

      <div className="feedback-header">
        {getMessage()}
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

      {/* Governor Warning - Physics/Resource violation */}
      {isGovernorWarning && feedback.reasoning && (
        <div className="governor-warning" data-testid="governor-warning">
          <strong>⚠️ Physics Warning:</strong>
          <p>{feedback.reasoning}</p>
        </div>
      )}

      {!isCorrect && !isGovernorWarning && getExplanation()}

      {getConcept()}

      {/* Score indicator for non-optimal bids */}
      {feedback.score !== undefined && feedback.score < 10 && (
        <div className="feedback-score">
          Score: {feedback.score.toFixed(1)}/10
        </div>
      )}

      {/* "Why?" button for differential analysis (only for non-optimal bids) */}
      {!isCorrect && (differentialData || handCards) && (
        <button
          className="feedback-why-button"
          onClick={() => setShowDifferential(!showDifferential)}
          aria-expanded={showDifferential}
          data-testid="feedback-why-button"
        >
          {showDifferential ? 'Hide details' : 'Why?'}
        </button>
      )}

      {/* Differential Analysis Panel (expanded view) */}
      {showDifferential && (
        <div className="feedback-differential-container" data-testid="differential-container">
          <DifferentialAnalysisPanel
            userBid={userBid}
            preloadedData={differentialData ? {
              user_bid: userBid,
              optimal_bid: feedback.optimal_bid,
              rating: correctnessLevel,
              score: feedback.score ? feedback.score * 10 : 50,
              differential: differentialData,
              physics: feedback.physics || differentialData?.physics,
              learning: feedback.learning || differentialData?.learning,
              commentary_html: feedback.commentary_html || differentialData?.commentary_html
            } : null}
            handCards={handCards}
            auctionHistory={auctionHistory}
            position={position}
            vulnerability={vulnerability}
            dealer={dealer}
            compact={true}
            onClose={() => setShowDifferential(false)}
          />
        </div>
      )}
    </div>
  );
};

export default BidFeedbackPanel;
