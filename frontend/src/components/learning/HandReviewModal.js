/**
 * HandReviewModal Component - Simplified 2-section hand analysis
 *
 * Sections:
 * 1. THE DEAL - 4-hand display + key stats (contract, accuracy %, tricks, DD expected)
 * 2. TRICK REPLAY - Interactive play-by-play with feedback inline
 *
 * Design Philosophy:
 * - Minimal sections for focused learning
 * - Deal section shows the hand + consolidated stats
 * - Trick replay is the main learning tool
 * - Mobile-friendly with natural scrolling
 *
 * Requires hand_id to be passed as prop.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PlayableCard } from '../play/PlayableCard';
import './HandReviewModal.css';

// ===== SECTION CARD COMPONENT =====
// Simple card wrapper for stacked layout - always visible (no accordion)
const SectionCard = ({
  id,
  title,
  subtitle,
  icon,
  headerRight,
  children
}) => {
  return (
    <div className="section-card" id={`section-${id}`}>
      <div className="section-card-header">
        <div className="section-title-group">
          {icon && <span className="section-icon">{icon}</span>}
          <div className="section-titles">
            <span className="section-title">{title}</span>
            {subtitle && <span className="section-subtitle">{subtitle}</span>}
          </div>
        </div>
        {headerRight && (
          <div className="section-header-right">{headerRight}</div>
        )}
      </div>
      <div className="section-card-content">
        {children}
      </div>
    </div>
  );
};

const API_BASE = process.env.REACT_APP_API_BASE || '';

// Rating colors and labels
const RATING_CONFIG = {
  optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '✓', label: 'Optimal' },
  good: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Good' },
  acceptable: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Acceptable' },
  suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
  blunder: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Blunder' },
  error: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Error' }
};

// Suit order (trump-aware for replay)
const getSuitOrder = (trumpStrain) => {
  if (!trumpStrain || trumpStrain === 'NT') {
    return ['♠', '♥', '♣', '♦'];
  }
  const strainToSuit = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
  const trumpSuit = strainToSuit[trumpStrain] || trumpStrain;
  if (trumpSuit === '♥') return ['♥', '♠', '♦', '♣'];
  if (trumpSuit === '♦') return ['♦', '♠', '♥', '♣'];
  if (trumpSuit === '♠') return ['♠', '♥', '♣', '♦'];
  if (trumpSuit === '♣') return ['♣', '♥', '♠', '♦'];
  return ['♠', '♥', '♣', '♦'];
};

// Sort cards within a hand by rank (high to low)
const sortCards = (cards) => {
  const rankOrder = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
  return [...cards].sort((a, b) => {
    const aRank = a.rank || a.r;
    const bRank = b.rank || b.r;
    return rankOrder.indexOf(aRank) - rankOrder.indexOf(bRank);
  });
};

// Normalize suit to Unicode format
const normalizeSuit = (suit) => {
  const map = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
  return map[suit] || suit;
};

// Hand display helper - shows a single player's hand using PlayableCard components
// Unified with Play-by-Play section for consistent visual style
const HandDisplay = ({ cards, position, isUser }) => {
  const suits = ['♠', '♥', '♦', '♣'];

  const cardsBySuit = useMemo(() => {
    const grouped = { '♠': [], '♥': [], '♦': [], '♣': [] };
    cards.forEach(card => {
      const suit = normalizeSuit(card.suit || card.s);
      if (grouped[suit]) {
        grouped[suit].push({
          rank: card.rank || card.r,
          suit: suit
        });
      }
    });

    // Sort each suit by rank
    const rankOrder = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
    Object.keys(grouped).forEach(suit => {
      grouped[suit].sort((a, b) => {
        return rankOrder.indexOf(a.rank) - rankOrder.indexOf(b.rank);
      });
    });

    return grouped;
  }, [cards]);

  return (
    <div className={`strategy-hand ${isUser ? 'user-hand' : ''}`}>
      <div className="strategy-hand-label">{position}</div>
      <div className="strategy-hand-cards">
        {suits.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (suitCards.length === 0) return null;
          return (
            <div key={suit} className="strategy-suit-group">
              {suitCards.map((card) => (
                <PlayableCard
                  key={`${card.rank}-${card.suit}`}
                  card={card}
                  disabled
                />
              ))}
            </div>
          );
        })}
        {cards.length === 0 && (
          <div className="strategy-hand-empty">No cards</div>
        )}
      </div>
    </div>
  );
};

// Replay hand display - shows remaining cards with visual PlayableCard components
// Horizontal layout for N/S, two-column vertical layout for E/W
const ReplayHandDisplay = ({ cards, position, trumpStrain, isVertical = false }) => {
  const suitOrder = getSuitOrder(trumpStrain);

  // Group and sort cards by suit
  const cardsBySuit = useMemo(() => {
    const grouped = { '♠': [], '♥': [], '♦': [], '♣': [] };
    cards.forEach(card => {
      const suit = normalizeSuit(card.suit || card.s);
      if (grouped[suit]) {
        grouped[suit].push({
          rank: card.rank || card.r,
          suit: suit
        });
      }
    });
    // Sort each suit
    Object.keys(grouped).forEach(suit => {
      grouped[suit] = sortCards(grouped[suit]);
    });
    return grouped;
  }, [cards]);

  const positionLabels = { N: 'North', E: 'East', S: 'South', W: 'West' };

  // For vertical (E/W) hands: split into 2 columns (♠♥ in col1, ♦♣ in col2)
  if (isVertical) {
    const col1Suits = suitOrder.filter(s => s === '♠' || s === '♥');
    const col2Suits = suitOrder.filter(s => s === '♦' || s === '♣');

    return (
      <div className={`replay-hand replay-hand-${position.toLowerCase()} vertical-2col`}>
        <div className="replay-hand-label">{positionLabels[position]}</div>
        <div className="replay-hand-2col">
          {/* Column 1: Spades + Hearts */}
          <div className="replay-col">
            {col1Suits.map(suit => {
              const suitCards = cardsBySuit[suit];
              return suitCards.map((card) => (
                <PlayableCard
                  key={`${card.rank}-${card.suit}`}
                  card={card}
                  disabled
                  compact
                />
              ));
            })}
          </div>
          {/* Column 2: Diamonds + Clubs */}
          <div className="replay-col">
            {col2Suits.map(suit => {
              const suitCards = cardsBySuit[suit];
              return suitCards.map((card) => (
                <PlayableCard
                  key={`${card.rank}-${card.suit}`}
                  card={card}
                  disabled
                  compact
                />
              ));
            })}
          </div>
        </div>
        {cards.length === 0 && (
          <div className="replay-hand-empty">No cards</div>
        )}
      </div>
    );
  }

  // Horizontal layout for N/S - show suit below rank (same as center trick display)
  return (
    <div className={`replay-hand replay-hand-${position.toLowerCase()} horizontal`}>
      <div className="replay-hand-label">{positionLabels[position]}</div>
      <div className="replay-hand-cards">
        {suitOrder.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (suitCards.length === 0) return null;
          return (
            <div key={suit} className="replay-suit-group">
              {suitCards.map((card) => (
                <PlayableCard
                  key={`${card.rank}-${card.suit}`}
                  card={card}
                  disabled
                  // No compact prop - show suit below rank for readability
                />
              ))}
            </div>
          );
        })}
        {cards.length === 0 && (
          <div className="replay-hand-empty">No cards</div>
        )}
      </div>
    </div>
  );
};

// Current trick display for replay mode - compass layout
const ReplayTrickDisplay = ({ trick, leader }) => {
  // Build position -> card map
  const cardByPosition = useMemo(() => {
    const map = { N: null, E: null, S: null, W: null };
    trick.forEach(play => {
      const pos = play.player || play.position;
      map[pos] = {
        rank: play.rank || play.r,
        suit: normalizeSuit(play.suit || play.s)
      };
    });
    return map;
  }, [trick]);

  const positions = [
    { pos: 'N', className: 'replay-trick-north' },
    { pos: 'W', className: 'replay-trick-west' },
    { pos: 'E', className: 'replay-trick-east' },
    { pos: 'S', className: 'replay-trick-south' }
  ];

  return (
    <div className="replay-trick-display">
      <div className="replay-trick-center">
        {leader && <span className="replay-trick-leader">Lead: {leader}</span>}
      </div>
      {positions.map(({ pos, className }) => (
        <div key={pos} className={className}>
          {cardByPosition[pos] ? (
            <div className="replay-trick-card-wrapper">
              <PlayableCard card={cardByPosition[pos]} disabled />
              <span className="replay-trick-position-label">{pos}</span>
            </div>
          ) : (
            <div className="replay-trick-empty" />
          )}
        </div>
      ))}
    </div>
  );
};

// Feedback panel for the current trick
const TrickFeedbackPanel = ({ decision }) => {
  if (!decision) {
    return (
      <div className="trick-feedback-panel no-data">
        <p>No analysis available for this play</p>
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

const HandReviewModal = ({
  handId,
  onClose,
  // Optional callbacks for action buttons (used when coming from post-hand flow)
  onPlayAnother,
  onReplay,
  onViewProgress,
  // Whether to show the result section prominently (true when replacing ScoreModal)
  showResultSection = false
}) => {
  const [handData, setHandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [replayPosition, setReplayPosition] = useState(0); // 0 to 52 (each card played)

  // No accordion state needed - all sections always visible in stacked layout

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

  // Get user-controlled positions (S always, plus dummy when NS declaring)
  const userControlledPositions = useMemo(() => {
    return handData?.user_controlled_positions || ['S'];
  }, [handData?.user_controlled_positions]);

  // Map decisions by trick number AND position for accurate lookup
  // Key format: "trick_position" e.g., "3_S" for trick 3, South's play
  const decisionsByTrickAndPosition = useMemo(() => {
    const map = {};
    if (handData?.play_quality_summary?.all_decisions) {
      handData.play_quality_summary.all_decisions.forEach(d => {
        // Only include decisions for positions the user controlled
        if (d.position && userControlledPositions.includes(d.position)) {
          const key = `${d.trick_number}_${d.position}`;
          map[key] = d;
        }
      });
    }
    return map;
  }, [handData?.play_quality_summary?.all_decisions, userControlledPositions]);


  // Get user position
  const userPosition = handData?.user_position || 'S';

  // Get trump strain from contract
  const trumpStrain = useMemo(() => {
    if (!handData?.contract) return 'NT';
    // Extract strain from contract like "3NT" or "4♠"
    const match = handData.contract.match(/\d([SHDC♠♥♦♣]|NT)/i);
    if (match) {
      const s = match[1].toUpperCase();
      if (s === 'NT') return 'NT';
      const strainMap = { 'S': 'S', '♠': 'S', 'H': 'H', '♥': 'H', 'D': 'D', '♦': 'D', 'C': 'C', '♣': 'C' };
      return strainMap[s] || 'NT';
    }
    return 'NT';
  }, [handData?.contract]);

  // Compute remaining hands at current replay position
  const remainingHands = useMemo(() => {
    if (!handData?.deal || !handData?.play_history) return null;

    // Start with full hands
    const hands = {
      N: [...(handData.deal.N?.hand || [])],
      E: [...(handData.deal.E?.hand || [])],
      S: [...(handData.deal.S?.hand || [])],
      W: [...(handData.deal.W?.hand || [])]
    };

    // Remove cards that have been played up to replayPosition
    const playsToRemove = handData.play_history.slice(0, replayPosition);
    playsToRemove.forEach(play => {
      const pos = play.player || play.position;
      const playRank = play.rank || play.r;
      const playSuit = normalizeSuit(play.suit || play.s);

      if (hands[pos]) {
        const idx = hands[pos].findIndex(c => {
          const cardRank = c.rank || c.r;
          const cardSuit = normalizeSuit(c.suit || c.s);
          return cardRank === playRank && cardSuit === playSuit;
        });
        if (idx !== -1) {
          hands[pos].splice(idx, 1);
        }
      }
    });

    return hands;
  }, [handData?.deal, handData?.play_history, replayPosition]);

  // Get current trick cards for replay (cards played in current trick at replayPosition)
  // replayPosition represents how many cards have been played (0 = none, 52 = all)
  // When position is 4, we should show all 4 cards of trick 1 (indices 0-3)
  const currentReplayTrick = useMemo(() => {
    if (!handData?.play_history || replayPosition === 0) return [];
    // Use replayPosition - 1 to get the index of the last card played
    const lastPlayedIdx = replayPosition - 1;
    const trickStartIdx = Math.floor(lastPlayedIdx / 4) * 4;
    const cardsInTrick = (lastPlayedIdx % 4) + 1; // +1 because we want to include the card at lastPlayedIdx
    return handData.play_history.slice(trickStartIdx, trickStartIdx + cardsInTrick);
  }, [handData?.play_history, replayPosition]);

  // Get the current trick number for replay (based on the last card played)
  const currentReplayTrickNumber = replayPosition === 0 ? 1 : Math.floor((replayPosition - 1) / 4) + 1;

  // Get leader for current replay trick
  const currentReplayLeader = useMemo(() => {
    if (!handData?.play_history || replayPosition === 0) return null;
    const lastPlayedIdx = replayPosition - 1;
    const trickStartIdx = Math.floor(lastPlayedIdx / 4) * 4;
    if (trickStartIdx < handData.play_history.length) {
      return handData.play_history[trickStartIdx]?.player || handData.play_history[trickStartIdx]?.position;
    }
    return null;
  }, [handData?.play_history, replayPosition]);

  // Get decision for current card being viewed in replay
  // Uses the precise trick_position key to get the correct decision
  const currentReplayDecision = useMemo(() => {
    if (!handData?.play_history || replayPosition === 0) return null;

    // Get the last played card's info
    const lastPlayedIdx = replayPosition - 1;
    const lastPlay = handData.play_history[lastPlayedIdx];
    if (!lastPlay) return null;

    const trickNum = Math.floor(lastPlayedIdx / 4) + 1;
    const position = lastPlay.player || lastPlay.position;

    // Only show decision if this position was controlled by user
    if (!userControlledPositions.includes(position)) return null;

    // Look up by trick_position key for precise matching
    const key = `${trickNum}_${position}`;
    return decisionsByTrickAndPosition[key] || null;
  }, [handData?.play_history, replayPosition, userControlledPositions, decisionsByTrickAndPosition]);

  // Total plays for navigation
  const totalPlays = handData?.play_history?.length || 0;

  // Navigate with keyboard - arrow keys control replay navigation
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }

    // Arrow keys navigate the replay (always available now with stacked layout)
    if (e.key === 'ArrowLeft' && replayPosition > 0) {
      setReplayPosition(p => p - 1);
    } else if (e.key === 'ArrowRight' && replayPosition < totalPlays) {
      setReplayPosition(p => p + 1);
    } else if (e.key === 'Home') {
      setReplayPosition(0);
    } else if (e.key === 'End') {
      setReplayPosition(totalPlays);
    }
  }, [replayPosition, totalPlays, onClose]);

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

  return (
    <div className="hand-review-modal-overlay" onClick={onClose}>
      <div className="hand-review-modal stacked-layout" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <h2>Hand Analysis</h2>
            <div className="contract-info">
              <span className="contract">{handData?.contract || 'Unknown'}</span>
              <span className={`result ${handData?.made ? 'made' : 'down'}`}>
                {handData?.made ? 'Made' : 'Down'}
                {handData?.tricks_taken !== undefined && handData?.tricks_needed !== undefined && (
                  <> ({handData.tricks_taken}/{handData.tricks_needed})</>
                )}
              </span>
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {/* Simplified 2-Section Layout */}
        <div className="modal-content stacked-container">

          {/* SECTION 1: THE DEAL - Hand display + consolidated stats */}
          <SectionCard
            id="deal"
            title="The Deal"
            subtitle={handData?.contract ? `${handData.contract} by ${handData.contract_declarer || 'South'}` : 'Hand overview'}
            icon="🃏"
            headerRight={
              <div className="deal-stats-header">
                {handData?.play_quality_summary?.has_data && (
                  <span className="accuracy-badge">{handData.play_quality_summary.accuracy_rate}% play</span>
                )}
                {handData?.bidding_quality_summary?.has_data && (
                  <span className="accuracy-badge bidding">{handData.bidding_quality_summary.accuracy_rate}% bid</span>
                )}
              </div>
            }
          >
            {/* Deal display - 4 hands in compass layout */}
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

            {/* Consolidated stats row */}
            <div className="deal-stats-consolidated">
              {/* Result */}
              <div className="stat-block">
                <span className="stat-label">Result</span>
                <span className={`stat-value ${handData?.made ? 'success' : 'danger'}`}>
                  {handData?.made ? 'Made' : 'Down'}
                  {handData?.tricks_taken !== undefined && handData?.tricks_needed !== undefined && (
                    <> ({handData.tricks_taken}/{handData.tricks_needed})</>
                  )}
                </span>
              </div>

              {/* DD Expected */}
              {handData?.par_comparison?.dd_tricks !== undefined && (
                <div className="stat-block">
                  <span className="stat-label">Perfect Play</span>
                  <span className="stat-value">{handData.par_comparison.dd_tricks} tricks</span>
                </div>
              )}

              {/* Score */}
              {handData?.hand_score !== undefined && (
                <div className="stat-block">
                  <span className="stat-label">Score</span>
                  <span className="stat-value">{handData.hand_score > 0 ? '+' : ''}{handData.hand_score}</span>
                </div>
              )}

              {/* Role */}
              <div className="stat-block">
                <span className="stat-label">Role</span>
                <span className="stat-value">
                  {handData?.user_role || (handData?.contract_declarer === userPosition ? 'Declarer' : 'Defender')}
                </span>
              </div>
            </div>

            {/* Action buttons if showing result */}
            {showResultSection && (onPlayAnother || onReplay || onViewProgress) && (
              <div className="result-actions">
                {onPlayAnother && (
                  <button className="action-btn primary" onClick={onPlayAnother}>
                    Play Another
                  </button>
                )}
                {onReplay && (
                  <button className="action-btn secondary" onClick={onReplay}>
                    Replay Hand
                  </button>
                )}
                {onViewProgress && (
                  <button className="action-btn secondary" onClick={onViewProgress}>
                    My Progress
                  </button>
                )}
              </div>
            )}
          </SectionCard>

          {/* SECTION 2: TRICK REPLAY - Interactive play-by-play with inline feedback */}
          {tricks.length > 0 && (
            <SectionCard
              id="trickReplay"
              title="Trick Replay"
              subtitle={`${totalTricks} tricks • Use ← → to navigate`}
              icon="▶️"
            >
              <div className="replay-mode">
                {/* Replay navigation */}
                <div className="replay-navigation">
                  <button
                    disabled={replayPosition <= 0}
                    onClick={() => setReplayPosition(0)}
                    aria-label="Go to start"
                    title="Go to start (Home)"
                  >
                    ⏮
                  </button>
                  <button
                    disabled={replayPosition <= 0}
                    onClick={() => setReplayPosition(p => p - 1)}
                    aria-label="Previous card"
                  >
                    ← Prev
                  </button>
                  <span className="replay-counter">
                    Play {replayPosition} of {totalPlays}
                    {replayPosition > 0 && (
                      <span className="trick-indicator"> (Trick {currentReplayTrickNumber})</span>
                    )}
                  </span>
                  <button
                    disabled={replayPosition >= totalPlays}
                    onClick={() => setReplayPosition(p => p + 1)}
                    aria-label="Next card"
                  >
                    Next →
                  </button>
                  <button
                    disabled={replayPosition >= totalPlays}
                    onClick={() => setReplayPosition(totalPlays)}
                    aria-label="Go to end"
                    title="Go to end (End)"
                  >
                    ⏭
                  </button>
                </div>

                {/* Replay table - traditional compass layout */}
                {remainingHands && (
                  <div className="replay-table-compass">
                    {/* North hand - top */}
                    <div className="replay-row replay-row-north">
                      <div className="replay-position">
                        <ReplayHandDisplay
                          cards={remainingHands.N}
                          position="N"
                          trumpStrain={trumpStrain}
                          isVertical={false}
                        />
                      </div>
                    </div>

                    {/* Middle row: West - Trick - East */}
                    <div className="replay-row replay-row-middle">
                      <div className="replay-position replay-west">
                        <ReplayHandDisplay
                          cards={remainingHands.W}
                          position="W"
                          trumpStrain={trumpStrain}
                          isVertical={true}
                        />
                      </div>

                      <div className="replay-center">
                        <ReplayTrickDisplay
                          trick={currentReplayTrick}
                          leader={currentReplayLeader}
                        />
                      </div>

                      <div className="replay-position replay-east">
                        <ReplayHandDisplay
                          cards={remainingHands.E}
                          position="E"
                          trumpStrain={trumpStrain}
                          isVertical={true}
                        />
                      </div>
                    </div>

                    {/* South hand - bottom */}
                    <div className="replay-row replay-row-south">
                      <div className="replay-position">
                        <ReplayHandDisplay
                          cards={remainingHands.S}
                          position="S"
                          trumpStrain={trumpStrain}
                          isVertical={false}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Feedback for current play if available */}
                {currentReplayDecision && replayPosition > 0 && (
                  <TrickFeedbackPanel decision={currentReplayDecision} />
                )}

                {/* Show hint when no decision available */}
                {replayPosition === 0 && (
                  <div className="replay-start-hint">
                    <p>Click <strong>Next →</strong> to step through each play and see feedback on your decisions.</p>
                  </div>
                )}
              </div>
            </SectionCard>
          )}
        </div>
      </div>
    </div>
  );
};

export default HandReviewModal;
