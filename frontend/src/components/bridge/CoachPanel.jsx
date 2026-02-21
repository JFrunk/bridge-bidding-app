import React, { useState } from 'react';
import { BidChip } from '../shared/BidChip';
import { SeatBeliefView } from './BeliefPanel';
import './CoachPanel.css';
import './BeliefPanel.css';  // Import for SeatBeliefView styles

/**
 * CoachPanel - Right sidebar coach assistant per UI Redesign bid-mockup-v2.html
 *
 * Only visible in Coached mode.
 * Contains collapsible sections:
 * - Partner's Likely Hand (HCP range, shape, suit lengths with colored symbols)
 * - Opponents' Hands (collapsed by default)
 * - Bid Explanation (what the auction means)
 * - "What Should I Bid?" hint button with AI suggestion
 */
export function CoachPanel({
  isVisible = true,
  onClose,
  beliefs,       // Raw beliefs object from backend { partner, lho, rho }
  onRequestHint,
  suggestedBid,  // { bid, explanation, loading, error }
  selectedBid,   // { bid, explanation, player } - clicked bid from auction history
  auction = [],
  myHcp,         // User's HCP for combined estimate
  handAnalysis   // User's hand analysis { totalPoints, hcp, dist, suits, suitQuality, balanced }
}) {
  const [expandedSections, setExpandedSections] = useState({
    partner: true,
    opponents: false,
    explanation: true
  });

  const [showMyHand, setShowMyHand] = useState(true);

  // Helper to check if a seat has meaningful beliefs
  const hasOpponentBeliefs = (belief) => {
    if (!belief) return false;
    return belief.hcp?.min > 0 || belief.hcp?.max < 40 || (belief.tags && belief.tags.length > 0);
  };

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
        {/* My Hand - Collapsible */}
        {handAnalysis && showMyHand && (
          <div className="coach-section my-hand-section">
            <div className="my-hand-header">
              <div className="my-hand-header-left">
                <span className="section-icon">🃏</span>
                <span className="my-hand-title">My Hand</span>
              </div>
              <button
                className="my-hand-close"
                onClick={() => setShowMyHand(false)}
                aria-label="Hide My Hand"
              >
                ×
              </button>
            </div>
            <div className="my-hand-content">
              {/* Line 1: Total Points, HCP, Dist, Balanced */}
              <div className="my-hand-summary">
                <span>Total Points {handAnalysis.totalPoints}</span>
                <span>HCP {handAnalysis.hcp}</span>
                <span>Dist {handAnalysis.dist}</span>
                <span>{handAnalysis.balanced ? 'Balanced' : 'Unbalanced'}</span>
              </div>

              {/* Line 2: HCP Bar */}
              <div className="my-hand-hcp-row">
                <div className="my-hand-hcp-bar-track">
                  <div
                    className="my-hand-hcp-bar-fill"
                    style={{
                      left: `${(handAnalysis.hcp / 40) * 100}%`,
                      width: '2%'
                    }}
                  />
                </div>
                <div className="my-hand-hcp-value">{handAnalysis.hcp}</div>
              </div>

              {/* Line 3: Suits */}
              <div className="my-hand-suits">
                <span className="suit-detail">
                  <span className="suit-black">♠</span> {handAnalysis.suits?.spades?.hcp || 0}({handAnalysis.suits?.spades?.length || 0})
                </span>
                <span className="suit-detail">
                  <span className="suit-red">♥</span> {handAnalysis.suits?.hearts?.hcp || 0}({handAnalysis.suits?.hearts?.length || 0})
                </span>
                <span className="suit-detail">
                  <span className="suit-red">♦</span> {handAnalysis.suits?.diamonds?.hcp || 0}({handAnalysis.suits?.diamonds?.length || 0})
                </span>
                <span className="suit-detail">
                  <span className="suit-black">♣</span> {handAnalysis.suits?.clubs?.hcp || 0}({handAnalysis.suits?.clubs?.length || 0})
                </span>
              </div>
            </div>
          </div>
        )}

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
              {beliefs?.partner && (beliefs.partner.hcp?.min > 0 || beliefs.partner.hcp?.max < 40 || beliefs.partner.tags?.length > 0) ? (
                <SeatBeliefView belief={beliefs.partner} showHow={false} />
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
              {(hasOpponentBeliefs(beliefs?.lho) || hasOpponentBeliefs(beliefs?.rho)) ? (
                <div className="opponent-info">
                  {/* LHO (Left-Hand Opponent) */}
                  {hasOpponentBeliefs(beliefs?.lho) && (
                    <div className="opponent-seat">
                      <div className="opponent-seat-label">
                        Left-Hand Opponent ({beliefs.lho.seat})
                      </div>
                      <SeatBeliefView belief={beliefs.lho} showHow={false} />
                    </div>
                  )}
                  {/* RHO (Right-Hand Opponent) */}
                  {hasOpponentBeliefs(beliefs?.rho) && (
                    <div className="opponent-seat">
                      <div className="opponent-seat-label">
                        Right-Hand Opponent ({beliefs.rho.seat})
                      </div>
                      <SeatBeliefView belief={beliefs.rho} showHow={false} />
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
              {selectedBid ? (
                // Show selected bid's explanation
                <div className="selected-bid-explanation">
                  <div className="selected-bid-header">
                    <BidChip bid={selectedBid.bid} />
                    <span className="selected-bid-by">by {selectedBid.player || 'Unknown'}</span>
                  </div>
                  <p className="explanation-text">
                    {selectedBid.explanation || 'No explanation available'}
                  </p>
                  <p className="explanation-hint">Click another bid to see its explanation</p>
                </div>
              ) : auction.length > 0 ? (
                // Show last bid's explanation by default
                <div className="selected-bid-explanation">
                  <div className="selected-bid-header">
                    <BidChip bid={auction[auction.length - 1].bid} />
                    <span className="selected-bid-by">by {auction[auction.length - 1].player || 'Unknown'}</span>
                  </div>
                  <p className="explanation-text">
                    {auction[auction.length - 1].explanation || 'No explanation available'}
                  </p>
                  <p className="explanation-hint">Click any bid in the auction to see its explanation</p>
                </div>
              ) : (
                <p className="no-info">Bid explanations will appear here as the auction progresses</p>
              )}
            </div>
          )}
        </div>

        {/* Suggested Bid Display */}
        {suggestedBid && !suggestedBid.loading && suggestedBid.bid && (
          <div className="coach-suggestion" data-testid="coach-suggestion">
            <div className="suggestion-header">
              <span className="suggestion-icon">💡</span>
              <span className="suggestion-label">Suggested Bid</span>
            </div>
            <div className="suggestion-bid">
              <BidChip bid={suggestedBid.bid} />
            </div>
            {suggestedBid.explanation && (
              <p className="suggestion-explanation">{suggestedBid.explanation}</p>
            )}
          </div>
        )}

        {/* Hint Button */}
        {onRequestHint && (
          <button
            className="hint-btn"
            onClick={onRequestHint}
            disabled={suggestedBid?.loading}
            data-testid="coach-hint-button"
          >
            <span className="hint-icon">💡</span>
            {suggestedBid?.loading ? 'Thinking...' : 'What Should I Bid?'}
          </button>
        )}
      </div>
    </div>
  );
}

export default CoachPanel;
