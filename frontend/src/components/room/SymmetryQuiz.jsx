/**
 * SymmetryQuiz - Post-Auction HCP Estimation Challenge
 *
 * P1 Feature: Both partners estimate each other's HCP before play begins.
 * Results displayed in two-column feedback pane to highlight system understanding.
 *
 * Flow:
 * 1. Host enables quiz toggle
 * 2. After auction ends (before play), both players submit HCP estimates
 * 3. Results shown with comparison to actual HCP
 */

import React, { useState } from 'react';
import './SymmetryQuiz.css';

// Calculate HCP from a hand array
function calculateHcp(hand) {
  if (!hand || !Array.isArray(hand)) return 0;
  const hcpValues = { 'A': 4, 'K': 3, 'Q': 2, 'J': 1 };
  return hand.reduce((total, card) => {
    const rank = card.rank || card.charAt(0);
    return total + (hcpValues[rank] || 0);
  }, 0);
}

export default function SymmetryQuiz({
  myHand,
  partnerHcp,
  onSubmit,
  onClose,
  showResults = false,
  myEstimate = null,
  partnerEstimate = null,
  isHost,
}) {
  const [estimate, setEstimate] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const myActualHcp = calculateHcp(myHand);

  const handleSubmit = (e) => {
    e.preventDefault();
    const hcpValue = parseInt(estimate, 10);
    if (isNaN(hcpValue) || hcpValue < 0 || hcpValue > 37) {
      return;
    }
    setSubmitted(true);
    onSubmit(hcpValue);
  };

  // Show results view
  if (showResults) {
    const myAccuracy = partnerHcp !== null && myEstimate !== null
      ? Math.abs(myEstimate - partnerHcp)
      : null;
    const partnerAccuracy = partnerEstimate !== null
      ? Math.abs(partnerEstimate - myActualHcp)
      : null;

    return (
      <div className="symmetry-quiz-overlay">
        <div className="symmetry-quiz-modal results">
          <div className="quiz-header">
            <h3>Partnership Estimate Results</h3>
            <button className="quiz-close" onClick={onClose}>×</button>
          </div>

          <div className="quiz-results-grid">
            {/* Your estimate of partner */}
            <div className="result-column you">
              <div className="result-label">Your Estimate of Partner</div>
              <div className="result-comparison">
                <div className="estimate-row">
                  <span className="estimate-label">Your guess:</span>
                  <span className="estimate-value">{myEstimate ?? '—'} HCP</span>
                </div>
                <div className="estimate-row actual">
                  <span className="estimate-label">Actual:</span>
                  <span className="estimate-value">{partnerHcp ?? '—'} HCP</span>
                </div>
                {myAccuracy !== null && (
                  <div className={`accuracy-badge ${myAccuracy <= 2 ? 'excellent' : myAccuracy <= 4 ? 'good' : 'off'}`}>
                    {myAccuracy === 0 ? 'Perfect!' : `Off by ${myAccuracy}`}
                  </div>
                )}
              </div>
            </div>

            {/* Partner's estimate of you */}
            <div className="result-column partner">
              <div className="result-label">Partner's Estimate of You</div>
              <div className="result-comparison">
                <div className="estimate-row">
                  <span className="estimate-label">Their guess:</span>
                  <span className="estimate-value">{partnerEstimate ?? '—'} HCP</span>
                </div>
                <div className="estimate-row actual">
                  <span className="estimate-label">Actual:</span>
                  <span className="estimate-value">{myActualHcp} HCP</span>
                </div>
                {partnerAccuracy !== null && (
                  <div className={`accuracy-badge ${partnerAccuracy <= 2 ? 'excellent' : partnerAccuracy <= 4 ? 'good' : 'off'}`}>
                    {partnerAccuracy === 0 ? 'Perfect!' : `Off by ${partnerAccuracy}`}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="quiz-insight">
            {myAccuracy !== null && partnerAccuracy !== null && (
              <p>
                {myAccuracy + partnerAccuracy <= 4
                  ? '✅ Great partnership communication!'
                  : myAccuracy + partnerAccuracy <= 8
                  ? '📊 Room for improvement in showing strength.'
                  : '⚠️ Review your bidding system together.'}
              </p>
            )}
          </div>

          <button className="btn-primary" onClick={onClose}>
            Continue to Play
          </button>
        </div>
      </div>
    );
  }

  // Waiting for partner view
  if (submitted) {
    return (
      <div className="symmetry-quiz-overlay">
        <div className="symmetry-quiz-modal waiting">
          <div className="quiz-header">
            <h3>Waiting for Partner...</h3>
          </div>
          <div className="quiz-waiting-content">
            <div className="waiting-spinner" />
            <p>You estimated: <strong>{estimate} HCP</strong></p>
            <p className="waiting-hint">Partner is making their estimate</p>
          </div>
        </div>
      </div>
    );
  }

  // Input view
  return (
    <div className="symmetry-quiz-overlay">
      <div className="symmetry-quiz-modal input">
        <div className="quiz-header">
          <h3>Partnership Challenge</h3>
        </div>

        <div className="quiz-prompt">
          <p>Based on the auction, estimate your partner's HCP:</p>
        </div>

        <form onSubmit={handleSubmit} className="quiz-form">
          <div className="hcp-input-wrapper">
            <input
              type="number"
              min="0"
              max="37"
              value={estimate}
              onChange={(e) => setEstimate(e.target.value)}
              placeholder="0-37"
              className="hcp-input"
              autoFocus
            />
            <span className="hcp-suffix">HCP</span>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={!estimate || parseInt(estimate, 10) < 0 || parseInt(estimate, 10) > 37}
          >
            Submit Estimate
          </button>
        </form>

        <p className="quiz-hint">
          Think about what partner's bids showed about their strength.
        </p>
      </div>
    </div>
  );
}

// Toggle component for host to enable quiz
export function SymmetryQuizToggle({ enabled, onToggle, disabled }) {
  return (
    <label className="symmetry-quiz-toggle" title="Challenge both players to estimate partner's HCP after auction">
      <input
        type="checkbox"
        checked={enabled}
        onChange={(e) => onToggle(e.target.checked)}
        disabled={disabled}
      />
      <span className="toggle-label">Partnership Quiz</span>
    </label>
  );
}
