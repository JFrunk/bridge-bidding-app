import React, { useState } from 'react';
import './CoachPanel.css';

/**
 * CoachPanel - Right sidebar coach assistant per UI Redesign bid-mockup-v2.html
 *
 * Only visible in Coached mode.
 * Contains collapsible sections:
 * - Partner's Likely Hand (HCP range, shape)
 * - Opponents' Hands (collapsed by default)
 * - Bid Explanation (what the auction means)
 * - "What Should I Bid?" hint button
 */
export function CoachPanel({
  isVisible = true,
  onClose,
  partnerInfo,
  opponentInfo,
  bidExplanation,
  onRequestHint,
  auction = []
}) {
  const [expandedSections, setExpandedSections] = useState({
    partner: true,
    opponents: false,
    explanation: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (!isVisible) return null;

  return (
    <div className="coach-column">
      {/* Header */}
      <div className="coach-header">
        <div className="coach-title">
          <span className="coach-icon">🎓</span>
          <span>Coach</span>
        </div>
        {onClose && (
          <button
            className="coach-close"
            onClick={onClose}
            aria-label="Close coach panel"
          >
            ×
          </button>
        )}
      </div>

      {/* Body */}
      <div className="coach-body">
        {/* Partner's Likely Hand */}
        <div className="coach-section">
          <button
            className="coach-section-header"
            onClick={() => toggleSection('partner')}
          >
            <span className="coach-section-title">
              <span className="section-icon">🔼</span>
              Partner's Likely Hand
            </span>
            <span className="coach-toggle">
              {expandedSections.partner ? '▾' : '▸'}
            </span>
          </button>
          {expandedSections.partner && (
            <div className="coach-section-body">
              {partnerInfo ? (
                <div className="partner-range">
                  <span className="label">HCP Range:</span>
                  <span className="value">{partnerInfo.hcpRange || '—'}</span>
                  <span className="label">Likely Shape:</span>
                  <span className="value">{partnerInfo.shape || '—'}</span>
                  {partnerInfo.notes && (
                    <>
                      <span className="label">Notes:</span>
                      <span className="value">{partnerInfo.notes}</span>
                    </>
                  )}
                </div>
              ) : (
                <p className="no-info">Make a bid to see partner analysis</p>
              )}
            </div>
          )}
        </div>

        {/* Opponents' Hands */}
        <div className="coach-section">
          <button
            className="coach-section-header"
            onClick={() => toggleSection('opponents')}
          >
            <span className="coach-section-title">
              <span className="section-icon">✕</span>
              Opponents' Hands
            </span>
            <span className="coach-toggle">
              {expandedSections.opponents ? '▾' : '▸'}
            </span>
          </button>
          {expandedSections.opponents && (
            <div className="coach-section-body">
              {opponentInfo ? (
                <div className="opponent-info">
                  {opponentInfo.east && (
                    <div className="opponent-row">
                      <span className="opp-label">East:</span>
                      <span className="opp-value">{opponentInfo.east}</span>
                    </div>
                  )}
                  {opponentInfo.west && (
                    <div className="opponent-row">
                      <span className="opp-label">West:</span>
                      <span className="opp-value">{opponentInfo.west}</span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="no-info">Opponent info appears as auction progresses</p>
              )}
            </div>
          )}
        </div>

        {/* Bid Explanation */}
        <div className="coach-section">
          <button
            className="coach-section-header"
            onClick={() => toggleSection('explanation')}
          >
            <span className="coach-section-title">
              <span className="section-icon">📝</span>
              Bid Explanation
            </span>
            <span className="coach-toggle">
              {expandedSections.explanation ? '▾' : '▸'}
            </span>
          </button>
          {expandedSections.explanation && (
            <div className="coach-section-body">
              {bidExplanation || auction.length > 0 ? (
                <p className="explanation-text">
                  {bidExplanation || generateExplanation(auction)}
                </p>
              ) : (
                <p className="no-info">Bid explanations will appear here as the auction progresses</p>
              )}
            </div>
          )}
        </div>

        {/* Hint Button */}
        {onRequestHint && (
          <button
            className="hint-btn"
            onClick={onRequestHint}
            data-testid="coach-hint-button"
          >
            <span className="hint-icon">💡</span>
            What Should I Bid?
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Generate a basic auction explanation from the bid history
 */
function generateExplanation(auction) {
  if (!auction || auction.length === 0) {
    return 'The auction has not started yet.';
  }

  const explanations = auction
    .filter(a => a.explanation)
    .map(a => `${a.bid}: ${a.explanation}`)
    .slice(-3); // Show last 3 explanations

  if (explanations.length === 0) {
    return 'Auction in progress...';
  }

  return explanations.join(' → ');
}

export default CoachPanel;
