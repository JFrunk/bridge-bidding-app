/**
 * HandReviewModal Component - Full hand replay with DDS analysis
 *
 * Features:
 * - Shows all 4 hands using game-consistent card display
 * - Displays auction and contract
 * - Step through play trick by trick with visual cards
 * - DDS feedback on each user play (optimal/good/suboptimal/blunder)
 * - Shows optimal alternative when play was suboptimal
 *
 * Requires hand_id to be passed as prop.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PlayableCard } from '../play/PlayableCard';
import './HandReviewModal.css';

const API_BASE = process.env.REACT_APP_API_BASE || '';

// Rating colors and labels
const RATING_CONFIG = {
  optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '✓', label: 'Optimal' },
  good: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Good' },
  suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
  blunder: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Blunder' }
};

// Normalize suit to Unicode format
const normalizeSuit = (suit) => {
  const map = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
  return map[suit] || suit;
};

// Hand display helper - shows a single player's hand in traditional format
const HandDisplay = ({ cards, position, isUser }) => {
  const suits = ['♠', '♥', '♦', '♣'];
  const suitColors = { '♠': '#000', '♥': '#dc2626', '♦': '#dc2626', '♣': '#000' };

  const cardsBySuit = useMemo(() => {
    const grouped = { '♠': [], '♥': [], '♦': [], '♣': [] };
    cards.forEach(card => {
      const suit = normalizeSuit(card.suit || card.s);
      if (grouped[suit]) {
        grouped[suit].push(card);
      }
    });

    // Sort each suit by rank
    const rankOrder = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
    Object.keys(grouped).forEach(suit => {
      grouped[suit].sort((a, b) => {
        const aRank = a.rank || a.r;
        const bRank = b.rank || b.r;
        return rankOrder.indexOf(aRank) - rankOrder.indexOf(bRank);
      });
    });

    return grouped;
  }, [cards]);

  return (
    <div className={`review-hand ${isUser ? 'user-hand' : ''}`}>
      <div className="hand-position">{position}</div>
      <div className="hand-suits">
        {suits.map(suit => (
          <div key={suit} className="suit-row">
            <span className="suit-symbol" style={{ color: suitColors[suit] }}>
              {suit}
            </span>
            <span className="suit-cards">
              {cardsBySuit[suit].length > 0
                ? cardsBySuit[suit].map((card, idx) => (
                    <span key={idx} className="card-rank">{card.rank || card.r}</span>
                  ))
                : <span className="card-void">—</span>
              }
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Visual card display with rating indicator
const AnalyzedCard = ({ card, decision, position, isUserPosition }) => {
  if (!card) return null;

  const normalizedCard = {
    rank: card.rank || card.r,
    suit: normalizeSuit(card.suit || card.s)
  };

  const rating = decision?.rating;
  const config = rating ? RATING_CONFIG[rating] : null;

  return (
    <div className={`analyzed-card-wrapper ${isUserPosition ? 'user-play' : ''}`}>
      <div className="position-label">{position}</div>
      <div className="card-with-rating">
        <PlayableCard card={normalizedCard} />
        {config && isUserPosition && (
          <div
            className={`rating-indicator rating-${rating}`}
            style={{ backgroundColor: config.color }}
            title={config.label}
          >
            {config.icon}
          </div>
        )}
      </div>
      {decision?.tricks_cost > 0 && isUserPosition && (
        <div className="tricks-lost-badge">
          -{decision.tricks_cost} trick{decision.tricks_cost !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

// Compass-style trick display using visual cards
const TrickDisplayVisual = ({ trick, trickNumber, decision, userPosition }) => {
  // Create position -> play mapping
  const playsByPosition = useMemo(() => {
    const map = {};
    trick.forEach(play => {
      const pos = play.player || play.position;
      map[pos] = play;
    });
    return map;
  }, [trick]);

  // Determine trick winner (simplified - just highlight if data available)
  const leader = trick[0]?.player || trick[0]?.position;

  return (
    <div className="trick-visual-display">
      <div className="trick-header">
        <span className="trick-label">Trick {trickNumber}</span>
        {leader && <span className="lead-indicator">Lead: {leader}</span>}
      </div>

      <div className="compass-layout">
        {/* North */}
        <div className="compass-north">
          <AnalyzedCard
            card={playsByPosition.N}
            position="N"
            decision={userPosition === 'N' ? decision : null}
            isUserPosition={userPosition === 'N'}
          />
        </div>

        {/* West and East row */}
        <div className="compass-middle">
          <div className="compass-west">
            <AnalyzedCard
              card={playsByPosition.W}
              position="W"
              decision={userPosition === 'W' ? decision : null}
              isUserPosition={userPosition === 'W'}
            />
          </div>
          <div className="compass-center" />
          <div className="compass-east">
            <AnalyzedCard
              card={playsByPosition.E}
              position="E"
              decision={userPosition === 'E' ? decision : null}
              isUserPosition={userPosition === 'E'}
            />
          </div>
        </div>

        {/* South */}
        <div className="compass-south">
          <AnalyzedCard
            card={playsByPosition.S}
            position="S"
            decision={userPosition === 'S' ? decision : null}
            isUserPosition={userPosition === 'S'}
          />
        </div>
      </div>
    </div>
  );
};

// Feedback panel for the current trick
const TrickFeedbackPanel = ({ decision }) => {
  if (!decision) {
    return (
      <div className="trick-feedback-panel no-data">
        <p>No DDS analysis available for this trick</p>
      </div>
    );
  }

  const config = RATING_CONFIG[decision.rating] || RATING_CONFIG.good;

  return (
    <div
      className={`trick-feedback-panel ${decision.rating}`}
      style={{ borderColor: config.color, backgroundColor: config.bgColor }}
    >
      <div className="feedback-header">
        <span className="feedback-badge" style={{ backgroundColor: config.color }}>
          {config.icon} {config.label}
        </span>
        {decision.tricks_cost > 0 && (
          <span className="tricks-cost">
            -{decision.tricks_cost} trick{decision.tricks_cost !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="feedback-body">
        <div className="play-comparison">
          <span className="played-card">
            <strong>You played:</strong> {decision.user_card}
          </span>
          {decision.optimal_card && decision.optimal_card !== decision.user_card && (
            <span className="optimal-card">
              <strong>Better:</strong> {decision.optimal_card}
            </span>
          )}
        </div>

        {decision.feedback && (
          <p className="feedback-text">{decision.feedback}</p>
        )}
      </div>
    </div>
  );
};

// Play Quality Summary display - shows overall hand performance
const PlayQualitySummary = ({ summary }) => {
  if (!summary || !summary.has_data) {
    return (
      <div className="play-quality-summary empty">
        <p className="no-data-message">{summary?.message || 'Play analysis not available for this hand'}</p>
      </div>
    );
  }

  const getRatingColor = (rate) => {
    if (rate >= 80) return '#059669';
    if (rate >= 60) return '#3b82f6';
    if (rate >= 40) return '#f59e0b';
    return '#dc2626';
  };

  return (
    <div className="play-quality-summary">
      <h4>Your Play Performance</h4>

      {/* Score gauge */}
      <div className="summary-gauge">
        <div className="gauge-score" style={{ color: getRatingColor(summary.accuracy_rate) }}>
          {summary.accuracy_rate}%
        </div>
        <div className="gauge-label">Accuracy ({summary.optimal_count + summary.good_count}/{summary.total_plays} plays)</div>
      </div>

      {/* Stats breakdown */}
      <div className="summary-stats">
        <div className="stat-pill optimal">
          <span className="stat-icon">✓</span>
          <span className="stat-count">{summary.optimal_count}</span>
          <span className="stat-label">Optimal</span>
        </div>
        <div className="stat-pill good">
          <span className="stat-icon">○</span>
          <span className="stat-count">{summary.good_count}</span>
          <span className="stat-label">Good</span>
        </div>
        <div className="stat-pill suboptimal">
          <span className="stat-icon">!</span>
          <span className="stat-count">{summary.suboptimal_count}</span>
          <span className="stat-label">Suboptimal</span>
        </div>
        <div className="stat-pill blunder">
          <span className="stat-icon">✗</span>
          <span className="stat-count">{summary.blunder_count}</span>
          <span className="stat-label">Blunder</span>
        </div>
      </div>

      {/* Tricks lost warning */}
      {summary.total_tricks_lost > 0 && (
        <div className="tricks-lost-warning">
          <span className="warning-icon">!</span>
          {summary.total_tricks_lost} trick{summary.total_tricks_lost !== 1 ? 's' : ''} lost from suboptimal plays
        </div>
      )}
    </div>
  );
};

const HandReviewModal = ({ handId, onClose }) => {
  const [handData, setHandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTrick, setCurrentTrick] = useState(1);

  // Fetch hand details
  useEffect(() => {
    const fetchHandDetail = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE}/api/hand-detail?hand_id=${handId}`);
        if (!response.ok) throw new Error('Failed to load hand');
        const data = await response.json();
        setHandData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (handId) {
      fetchHandDetail();
    }
  }, [handId]);

  // Group plays into tricks
  const tricks = useMemo(() => {
    if (!handData?.play_history) return [];
    const result = [];
    for (let i = 0; i < handData.play_history.length; i += 4) {
      result.push(handData.play_history.slice(i, i + 4));
    }
    return result;
  }, [handData?.play_history]);

  // Map decisions by trick number for quick lookup
  const decisionsByTrick = useMemo(() => {
    const map = {};
    if (handData?.play_quality_summary?.all_decisions) {
      handData.play_quality_summary.all_decisions.forEach(d => {
        map[d.trick_number] = d;
      });
    }
    return map;
  }, [handData?.play_quality_summary?.all_decisions]);

  // Get user position
  const userPosition = handData?.user_position || 'S';

  // Navigate tricks with keyboard
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowLeft' && currentTrick > 1) {
      setCurrentTrick(t => t - 1);
    } else if (e.key === 'ArrowRight' && currentTrick < tricks.length) {
      setCurrentTrick(t => t + 1);
    } else if (e.key === 'Escape') {
      onClose();
    }
  }, [currentTrick, tricks.length, onClose]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (loading) {
    return (
      <div className="hand-review-modal-overlay" onClick={onClose}>
        <div className="hand-review-modal" onClick={e => e.stopPropagation()}>
          <div className="loading-state">Loading hand...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="hand-review-modal-overlay" onClick={onClose}>
        <div className="hand-review-modal" onClick={e => e.stopPropagation()}>
          <div className="error-state">
            <p>Error: {error}</p>
            <button onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  const totalTricks = tricks.length;
  const currentDecision = decisionsByTrick[currentTrick];

  return (
    <div className="hand-review-modal-overlay" onClick={onClose}>
      <div className="hand-review-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <h2>Hand Review</h2>
            <div className="contract-info">
              <span className="contract">{handData?.contract || 'Unknown'}</span>
              <span className={`result ${handData?.made ? 'made' : 'down'}`}>
                {handData?.made ? 'Made' : 'Down'}
                {handData?.tricks_taken !== undefined && handData?.tricks_needed !== undefined && (
                  <> ({handData.tricks_taken} / {handData.tricks_needed})</>
                )}
              </span>
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {/* Main content */}
        <div className="modal-content">
          {/* Deal display - 4 hands */}
          {handData?.deal && (
            <div className="deal-display">
              <div className="north-position">
                <HandDisplay
                  cards={handData.deal.N?.hand || []}
                  position="North"
                  isUser={userPosition === 'N'}
                />
              </div>
              <div className="ew-row">
                <HandDisplay
                  cards={handData.deal.W?.hand || []}
                  position="West"
                  isUser={userPosition === 'W'}
                />
                <div className="center-info">
                  <div className="vulnerability">
                    Vul: {handData.vulnerability || 'None'}
                  </div>
                  <div className="dealer">
                    Dealer: {handData.dealer}
                  </div>
                </div>
                <HandDisplay
                  cards={handData.deal.E?.hand || []}
                  position="East"
                  isUser={userPosition === 'E'}
                />
              </div>
              <div className="south-position">
                <HandDisplay
                  cards={handData.deal.S?.hand || []}
                  position="South"
                  isUser={userPosition === 'S'}
                />
              </div>
            </div>
          )}

          {/* Play Quality Summary - shows overall performance for this hand */}
          <PlayQualitySummary summary={handData?.play_quality_summary} />

          {/* Play-by-play section */}
          {tricks.length > 0 && (
            <div className="play-history-section">
              <h3>Play-by-Play Analysis</h3>

              {/* Trick navigation */}
              <div className="trick-navigation">
                <button
                  disabled={currentTrick <= 1}
                  onClick={() => setCurrentTrick(t => t - 1)}
                  aria-label="Previous trick"
                >
                  ← Prev
                </button>
                <span className="trick-counter">Trick {currentTrick} of {totalTricks}</span>
                <button
                  disabled={currentTrick >= totalTricks}
                  onClick={() => setCurrentTrick(t => t + 1)}
                  aria-label="Next trick"
                >
                  Next →
                </button>
              </div>

              {/* Visual trick display */}
              <TrickDisplayVisual
                trick={tricks[currentTrick - 1] || []}
                trickNumber={currentTrick}
                decision={currentDecision}
                userPosition={userPosition}
              />

              {/* Feedback panel */}
              <TrickFeedbackPanel decision={currentDecision} />

              <p className="navigation-hint">Use arrow keys ← → to navigate tricks</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HandReviewModal;
