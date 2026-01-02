/**
 * HandReviewModal Component - Full hand replay with DDS analysis
 *
 * Features:
 * - Shows all 4 hands
 * - Displays auction and contract
 * - Step through play trick by trick
 * - Click on any play to get DDS analysis
 * - Opening lead analysis button
 *
 * Requires hand_id to be passed as prop.
 */

import React, { useState, useEffect, useCallback } from 'react';
import './HandReviewModal.css';

const API_BASE = process.env.REACT_APP_API_BASE || '';

// Card display helper
const CardDisplay = ({ rank, suit, onClick, isHighlighted, isPlayed }) => {
  // Support both letter format ('S', 'H', 'D', 'C') and Unicode format ('♠', '♥', '♦', '♣')
  const suitSymbols = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣', '♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣' };
  const suitColors = { 'S': '#000', 'H': '#dc2626', 'D': '#dc2626', 'C': '#000', '♠': '#000', '♥': '#dc2626', '♦': '#dc2626', '♣': '#000' };
  const symbol = suitSymbols[suit] || suit;
  const color = suitColors[suit] || '#000';

  return (
    <span
      className={`review-card ${isHighlighted ? 'highlighted' : ''} ${isPlayed ? 'played' : ''} ${onClick ? 'clickable' : ''}`}
      style={{ color }}
      onClick={onClick}
    >
      {rank}{symbol}
    </span>
  );
};

// Hand display helper - shows a single player's hand
const HandDisplay = ({ cards, position, isUser, onClick }) => {
  // Group cards by suit - support both letter and Unicode formats
  const suits = ['S', 'H', 'D', 'C'];
  const suitSymbols = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
  // Map Unicode suits back to letter format for grouping
  const unicodeToLetter = { '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' };

  const cardsBySuit = {};
  suits.forEach(s => cardsBySuit[s] = []);

  cards.forEach(card => {
    let suit = card.suit || card.s;
    // Normalize Unicode suits to letter format
    suit = unicodeToLetter[suit] || suit;
    if (cardsBySuit[suit]) {
      cardsBySuit[suit].push(card);
    }
  });

  // Sort each suit by rank
  const rankOrder = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
  Object.keys(cardsBySuit).forEach(suit => {
    cardsBySuit[suit].sort((a, b) => {
      const aRank = a.rank || a.r;
      const bRank = b.rank || b.r;
      return rankOrder.indexOf(aRank) - rankOrder.indexOf(bRank);
    });
  });

  return (
    <div className={`review-hand ${isUser ? 'user-hand' : ''}`}>
      <div className="hand-position">{position}</div>
      <div className="hand-suits">
        {suits.map(suit => (
          <div key={suit} className="suit-row">
            <span className="suit-symbol" style={{ color: suit === 'H' || suit === 'D' ? '#dc2626' : '#000' }}>
              {suitSymbols[suit]}
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

// Trick display helper
const TrickDisplay = ({ trick, trickNumber, onCardClick, analyzedPlay }) => {
  const positions = ['N', 'E', 'S', 'W'];

  return (
    <div className="trick-display">
      <div className="trick-number">Trick {trickNumber}</div>
      <div className="trick-cards">
        {positions.map((pos, idx) => {
          const play = trick.find(p => (p.player || p.position) === pos);
          if (!play) return <div key={pos} className="trick-card empty" />;

          const isAnalyzed = analyzedPlay &&
            analyzedPlay.trick_number === trickNumber &&
            analyzedPlay.play_index === idx;

          return (
            <div
              key={pos}
              className={`trick-card ${isAnalyzed ? 'analyzed' : ''}`}
              onClick={() => onCardClick && onCardClick(trickNumber, idx)}
            >
              <div className="trick-card-position">{pos}</div>
              <CardDisplay
                rank={play.rank || play.r}
                suit={play.suit || play.s}
                onClick={() => onCardClick && onCardClick(trickNumber, idx)}
                isHighlighted={isAnalyzed}
              />
            </div>
          );
        })}
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
          <span className="stat-icon">⚠</span>
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
          <span className="warning-icon">⚠</span>
          {summary.total_tricks_lost} trick{summary.total_tricks_lost !== 1 ? 's' : ''} lost from suboptimal plays
        </div>
      )}

      {/* Notable mistakes */}
      {summary.notable_mistakes && summary.notable_mistakes.length > 0 && (
        <div className="notable-mistakes">
          <h5>Key Learning Moments</h5>
          {summary.notable_mistakes.map((mistake, idx) => (
            <div key={idx} className={`mistake-item ${mistake.rating}`}>
              <div className="mistake-header">
                <span className="trick-num">Trick {mistake.trick_number}</span>
                <span className="rating-badge">{mistake.rating}</span>
              </div>
              <div className="mistake-detail">
                <span className="played">Played: {mistake.user_card}</span>
                {mistake.optimal_card && (
                  <span className="optimal">Better: {mistake.optimal_card}</span>
                )}
                {mistake.tricks_cost > 0 && (
                  <span className="cost">-{mistake.tricks_cost} trick{mistake.tricks_cost !== 1 ? 's' : ''}</span>
                )}
              </div>
              {mistake.feedback && (
                <div className="mistake-feedback">{mistake.feedback}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Trick Analysis display - shows analysis of a specific card play
const TrickAnalysis = ({ analysis, onClose }) => {
  if (!analysis) return null;

  const getRatingColor = (rating) => {
    switch (rating) {
      case 'optimal': return '#059669';
      case 'good': return '#3b82f6';
      case 'suboptimal': return '#f59e0b';
      case 'blunder': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getRatingLabel = (rating) => {
    switch (rating) {
      case 'optimal': return 'Optimal Play';
      case 'good': return 'Good Play';
      case 'suboptimal': return 'Could Be Better';
      case 'blunder': return 'Costly Mistake';
      default: return 'Unknown';
    }
  };

  return (
    <div className="trick-analysis-panel">
      <div className="trick-analysis-header">
        <h4>
          {analysis.is_opening_lead ? 'Opening Lead Analysis' : `Trick ${analysis.trick_number} Analysis`}
        </h4>
        <button className="trick-analysis-close-btn" onClick={onClose}>×</button>
      </div>

      {!analysis.dds_available ? (
        <div className="analysis-unavailable">
          <p>{analysis.message || 'Analysis not available for this play'}</p>
        </div>
      ) : (
        <div className="trick-analysis-content">
          {/* Rating badge */}
          <div className="analysis-rating" style={{ backgroundColor: getRatingColor(analysis.rating) }}>
            {getRatingLabel(analysis.rating)}
          </div>

          {/* Your play */}
          <div className="your-play-info">
            <span className="label">You played:</span>
            <CardDisplay
              rank={analysis.actual_play?.rank || analysis.actual_play?.r}
              suit={analysis.actual_play?.suit || analysis.actual_play?.s}
            />
            {analysis.tricks_lost > 0 && (
              <span className="tricks-lost">
                ({analysis.tricks_lost} trick{analysis.tricks_lost !== 1 ? 's' : ''} lost)
              </span>
            )}
          </div>

          {/* Alternatives */}
          {analysis.alternatives && analysis.alternatives.length > 0 && (
            <div className="play-alternatives">
              <div className="alternatives-header">All options ranked:</div>
              <div className="alternatives-list">
                {analysis.alternatives.slice(0, 5).map((alt, idx) => (
                  <div
                    key={idx}
                    className={`alternative-card ${alt.is_actual ? 'is-actual' : ''}`}
                  >
                    <CardDisplay rank={alt.card?.rank} suit={alt.card?.suit} />
                    <span className="alt-tricks">{alt.tricks} tricks</span>
                    {idx === 0 && !alt.is_actual && <span className="best-label">Best</span>}
                    {alt.is_actual && <span className="your-label">Yours</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
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
  const [analyzedPlay, setAnalyzedPlay] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

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

  // Analyze a specific play
  const analyzePlay = useCallback(async (trickNumber, playIndex) => {
    if (!handId) return;

    try {
      setAnalyzing(true);
      const response = await fetch(`${API_BASE}/api/analyze-play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hand_id: handId,
          trick_number: trickNumber,
          play_index: playIndex
        })
      });

      if (!response.ok) throw new Error('Failed to analyze play');
      const data = await response.json();
      setAnalyzedPlay(data);
    } catch (err) {
      console.error('Analysis error:', err);
      setAnalyzedPlay({ error: err.message, dds_available: false });
    } finally {
      setAnalyzing(false);
    }
  }, [handId]);

  // Analyze opening lead
  const analyzeOpeningLead = useCallback(() => {
    analyzePlay(1, 0);
  }, [analyzePlay]);

  // Group plays into tricks
  const getTricks = () => {
    if (!handData?.play_history) return [];
    const tricks = [];
    for (let i = 0; i < handData.play_history.length; i += 4) {
      tricks.push(handData.play_history.slice(i, i + 4));
    }
    return tricks;
  };

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

  const tricks = getTricks();
  const totalTricks = tricks.length;

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
                  isUser={handData.user_position === 'N'}
                />
              </div>
              <div className="ew-row">
                <HandDisplay
                  cards={handData.deal.W?.hand || []}
                  position="West"
                  isUser={handData.user_position === 'W'}
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
                  isUser={handData.user_position === 'E'}
                />
              </div>
              <div className="south-position">
                <HandDisplay
                  cards={handData.deal.S?.hand || []}
                  position="South"
                  isUser={handData.user_position === 'S'}
                />
              </div>
            </div>
          )}

          {/* Play Quality Summary - shows overall performance for this hand */}
          <PlayQualitySummary summary={handData?.play_quality_summary} />

          {/* Action buttons */}
          <div className="analysis-actions">
            <button
              className="analyze-lead-btn"
              onClick={analyzeOpeningLead}
              disabled={analyzing || !handData?.play_history?.length}
            >
              {analyzing ? 'Analyzing...' : 'Analyze Opening Lead'}
            </button>
          </div>

          {/* Trick Analysis panel */}
          {analyzedPlay && (
            <TrickAnalysis
              analysis={analyzedPlay}
              onClose={() => setAnalyzedPlay(null)}
            />
          )}

          {/* Play history */}
          {tricks.length > 0 && (
            <div className="play-history-section">
              <h3>Play-by-Play</h3>
              <div className="trick-navigation">
                <button
                  disabled={currentTrick <= 1}
                  onClick={() => setCurrentTrick(t => t - 1)}
                >
                  &lt; Prev
                </button>
                <span>Trick {currentTrick} of {totalTricks}</span>
                <button
                  disabled={currentTrick >= totalTricks}
                  onClick={() => setCurrentTrick(t => t + 1)}
                >
                  Next &gt;
                </button>
              </div>

              <TrickDisplay
                trick={tricks[currentTrick - 1] || []}
                trickNumber={currentTrick}
                onCardClick={analyzePlay}
                analyzedPlay={analyzedPlay}
              />

              <p className="click-hint">Click any card to analyze that play</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HandReviewModal;
