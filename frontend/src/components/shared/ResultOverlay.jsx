/**
 * ResultOverlay Component
 *
 * Floating overlay that displays hand results after play is complete.
 * Positioned absolutely over the game board with high z-index.
 *
 * Uses "Clubhouse" aesthetic:
 * - Deep Green header
 * - Cream body
 * - Clear button separation
 */

import React, { useState, useEffect } from 'react';
import { ScoreBreakdown } from '../play/ScoreBreakdown';
import { BidChip } from './BidChip';
import { ChevronDown, ChevronUp } from 'lucide-react';
import './ResultOverlay.css';

const ResultOverlay = ({
  scoreData,           // Score data from API
  isVisible,           // Whether to show the overlay (gameState.isHandComplete === true)
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
      // Small delay for smooth animation
      const showTimer = setTimeout(() => setIsShowing(true), 100);
      return () => clearTimeout(showTimer);
    } else {
      setIsShowing(false);
      setShowBreakdown(false);
    }
  }, [isVisible, scoreData]);

  if (!isVisible || !scoreData) return null;

  const { contract, tricks_taken, tricks_needed, score, made, breakdown, overtricks, undertricks } = scoreData;
  const doubledText = contract?.doubled === 2 ? 'XX' : contract?.doubled === 1 ? 'X' : '';

  // Score perspective adjustment (user always plays NS)
  const declarerIsNS = contract?.declarer === 'N' || contract?.declarer === 'S';
  const userScore = declarerIsNS ? score : -score;
  const userMade = declarerIsNS ? made : !made;

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
    return 'Made';
  };

  return (
    <div
      className={`result-overlay-backdrop ${isShowing ? 'showing' : ''}`}
      data-testid="result-overlay"
    >
      <div className={`result-overlay ${userMade ? 'result-success' : 'result-failure'}`}>
        {/* Deep Green Header */}
        <div className="result-overlay-header">
          <div className="header-content">
            <BidChip bid={getContractDisplay()} size="lg" />
            <span className="header-by">by {contract?.declarer}</span>
            {contract?.vulnerability && (
              <span className="header-vuln">{contract.vulnerability}</span>
            )}
          </div>
          <div className="header-stats">
            <span>NS: {scoreData.ns_tricks || tricks_taken}</span>
            <span className="stat-divider">•</span>
            <span>EW: {scoreData.ew_tricks || (13 - tricks_taken)}</span>
            <span className="stat-divider">•</span>
            <span>Need {tricks_needed}</span>
            <span className="stat-divider">•</span>
            <span>Trick 14/13</span>
          </div>
        </div>

        {/* Cream Body */}
        <div className="result-overlay-body">
          {/* Tricks row */}
          <div className="result-row">
            <span className="row-label">Tricks:</span>
            <span className="row-value">{tricks_taken} of {tricks_needed} needed</span>
          </div>

          {/* Result row */}
          <div className="result-row">
            <span className="row-label">Result:</span>
            <span className={`row-value ${userMade ? 'text-success' : 'text-failure'}`}>
              {getResultDescription()}
            </span>
          </div>

          {/* Score display */}
          <div className={`result-score ${userScore >= 0 ? 'score-positive' : 'score-negative'}`}>
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

          {/* Primary Action Button */}
          <button
            className="action-btn action-primary"
            onClick={onPlayAnotherHand}
            data-testid="result-play-another"
          >
            Play Another Hand
          </button>

          {/* Secondary Action Buttons - Review vs Next */}
          <div className="action-row-secondary">
            {onReviewHand && (
              <button
                className="action-btn action-secondary"
                onClick={onReviewHand}
                data-testid="result-review"
              >
                Review Hand
              </button>
            )}
            {onViewProgress && (
              <button
                className="action-btn action-secondary"
                onClick={onViewProgress}
                data-testid="result-progress"
              >
                My Progress
              </button>
            )}
          </div>

          {/* Tertiary Actions - Smaller, less prominent */}
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
    </div>
  );
};

export default ResultOverlay;
