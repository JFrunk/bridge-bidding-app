/**
 * HandReviewModal Component - Unified hand analysis with play-by-play
 *
 * Single consolidated view that:
 * 1. Shows all 4 hands dealt (initial view)
 * 2. Offers navigation to step through each play
 * 3. Shows feedback inline as you navigate
 *
 * Design Philosophy:
 * - Single pane, single interaction pattern
 * - Start at position 0 showing all dealt hands
 * - Use arrow keys or buttons to step through play-by-play
 * - Mobile-friendly with natural scrolling
 *
 * Requires hand_id to be passed as prop.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PlayableCard } from '../play/PlayableCard';
import DecayChart from '../analysis/DecayChart';
import './HandReviewModal.css';

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

  // Handle basic info (when no DDS analysis was recorded)
  if (decision.is_basic_info) {
    const positionName = decision.position === 'N' ? 'North' :
                         decision.position === 'S' ? 'South' :
                         decision.position === 'E' ? 'East' : 'West';
    return (
      <div className="trick-feedback-panel basic-info" style={{
        borderColor: '#6b7280',
        backgroundColor: '#f9fafb'
      }}>
        <div className="feedback-body">
          <div className="play-comparison">
            <span className="played-card">
              <strong>{positionName} played:</strong> {decision.user_card}
            </span>
          </div>
          <p className="feedback-text" style={{ color: '#6b7280', fontStyle: 'italic' }}>
            Trick {decision.trick_number} • No detailed analysis recorded
          </p>
        </div>
      </div>
    );
  }

  const config = RATING_CONFIG[decision.rating] || RATING_CONFIG.good;
  const positionName = decision.position === 'N' ? 'North' :
                       decision.position === 'S' ? 'South' :
                       decision.position === 'E' ? 'East' : 'West';

  return (
    <div
      className={`trick-feedback-panel ${decision.rating}`}
      style={{ borderColor: config.color, backgroundColor: config.bgColor }}
    >
      <div className="feedback-header">
        <span className="feedback-badge" style={{ backgroundColor: config.color }}>
          {config.icon} {config.label}
        </span>
        <span className="position-indicator" style={{ marginLeft: '8px', color: '#6b7280' }}>
          ({positionName})
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
            <strong>{positionName} played:</strong> {decision.user_card}
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
  // Shows info for all user-controlled positions (both N and S when NS declares)
  const currentReplayDecision = useMemo(() => {
    if (!handData?.play_history || replayPosition === 0) return null;

    // Get the last played card's info
    const lastPlayedIdx = replayPosition - 1;
    const lastPlay = handData.play_history[lastPlayedIdx];
    if (!lastPlay) return null;

    const trickNum = Math.floor(lastPlayedIdx / 4) + 1;
    const position = lastPlay.player || lastPlay.position;

    // Only show decision/info if this position was controlled by user
    if (!userControlledPositions.includes(position)) return null;

    // Look up by trick_position key for precise matching
    const key = `${trickNum}_${position}`;
    const storedDecision = decisionsByTrickAndPosition[key];

    // If we have a stored decision, return it
    if (storedDecision) return storedDecision;

    // If no stored decision but this is a user-controlled position,
    // create a minimal info object so we can still show the play
    const cardRank = lastPlay.rank || lastPlay.r;
    const cardSuit = normalizeSuit(lastPlay.suit || lastPlay.s);
    return {
      position: position,
      trick_number: trickNum,
      user_card: `${cardRank}${cardSuit}`,
      // No rating/score since we don't have DDS analysis
      rating: null,
      score: null,
      feedback: `${position === 'N' ? 'North' : 'South'} played ${cardRank}${cardSuit}`,
      is_basic_info: true  // Flag to indicate this is synthetic, not from DB
    };
  }, [handData?.play_history, replayPosition, userControlledPositions, decisionsByTrickAndPosition]);

  // Total plays for navigation
  const totalPlays = handData?.play_history?.length || 0;

  // Determine user's role and perspective
  const userRole = useMemo(() => {
    if (!handData) return 'Unknown';
    if (handData.user_role) return handData.user_role;
    const declarer = handData.contract_declarer;
    if (declarer === 'S' || declarer === 'N') return 'Declarer';
    return 'Defender';
  }, [handData]);

  const isUserDefender = userRole === 'Defender';

  // Get declarer name for display
  const getDeclarerName = (d) => {
    if (d === 'N') return 'North';
    if (d === 'S') return 'South';
    if (d === 'E') return 'East';
    if (d === 'W') return 'West';
    return d;
  };

  // Convert score from declarer's perspective to NS (user's) perspective
  const getScoreForUser = () => {
    const score = handData?.hand_score || 0;
    const declarer = handData?.contract_declarer;
    // If declarer is EW, negate the score for NS perspective
    if (declarer === 'E' || declarer === 'W') {
      return -score;
    }
    return score;
  };

  // Get result display from user's perspective
  const getResultForUser = () => {
    const tricksTaken = handData?.tricks_taken;
    const tricksNeeded = handData?.tricks_needed;
    const made = handData?.made;

    if (tricksTaken === undefined || tricksNeeded === undefined) {
      if (isUserDefender) {
        // Defender: opponents made/down
        return made ? { text: 'Opponents Made', isGood: false } : { text: 'Set Contract', isGood: true };
      } else {
        return made ? { text: 'Made', isGood: true } : { text: 'Down', isGood: false };
      }
    }

    if (isUserDefender) {
      // As defender: show from defensive perspective
      if (made) {
        const over = tricksTaken - tricksNeeded;
        if (over > 0) {
          return { text: `Opponents Made +${over}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: false };
        }
        return { text: 'Opponents Made', detail: `(${tricksTaken}/${tricksNeeded})`, isGood: false };
      } else {
        const down = tricksNeeded - tricksTaken;
        return { text: `Set ${down}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: true };
      }
    } else {
      // As declarer/dummy
      if (made) {
        const over = tricksTaken - tricksNeeded;
        if (over > 0) {
          return { text: `Made +${over}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: true };
        }
        return { text: 'Made', detail: `(${tricksTaken}/${tricksNeeded})`, isGood: true };
      } else {
        const down = tricksNeeded - tricksTaken;
        return { text: `Down ${down}`, detail: `(${tricksTaken}/${tricksNeeded})`, isGood: false };
      }
    }
  };

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

  return (
    <div className="hand-review-modal-overlay" onClick={onClose}>
      <div className="hand-review-modal unified-layout" onClick={e => e.stopPropagation()}>
        {/* Header with contract info and accuracy badges */}
        <div className="modal-header">
          <div className="modal-title">
            <h2>Hand Analysis</h2>
            <div className="contract-info">
              <span className="contract">
                {handData?.contract || 'Unknown'} by {getDeclarerName(handData?.contract_declarer)}
              </span>
              {(() => {
                const result = getResultForUser();
                return (
                  <span className={`result ${result.isGood ? 'made' : 'down'}`}>
                    {result.text}
                    {result.detail && <> {result.detail}</>}
                  </span>
                );
              })()}
              {handData?.play_quality_summary?.has_data && (
                <span className="accuracy-badge">{handData.play_quality_summary.accuracy_rate}% play</span>
              )}
              {handData?.bidding_quality_summary?.has_data && (
                <span className="accuracy-badge bidding">{handData.bidding_quality_summary.accuracy_rate}% bid</span>
              )}
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {/* Unified content - single pane with play-by-play navigation */}
        <div className="modal-content unified-container">
          {/* Navigation controls - always visible at top */}
          {tricks.length > 0 && (
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
                {replayPosition === 0 ? (
                  'Start • All cards dealt'
                ) : (
                  <>
                    Play {replayPosition} of {totalPlays}
                    <span className="trick-indicator"> (Trick {currentReplayTrickNumber})</span>
                  </>
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
          )}

          {/* Decay Chart - shows trick potential over time */}
          {handData?.decay_curve && (
            <DecayChart
              data={handData.decay_curve}
              replayPosition={replayPosition}
              onPositionChange={setReplayPosition}
            />
          )}

          {/* Main display area - compass layout with hands */}
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

              {/* Middle row: West - Trick/Info - East */}
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
                  {replayPosition === 0 ? (
                    /* Center info when showing initial deal */
                    <div className="center-info-box">
                      <div className="center-contract">{handData?.contract}</div>
                      <div className="center-vulnerability">Vul: {handData?.vulnerability || 'None'}</div>
                      <div className="center-dealer">Dealer: {handData?.dealer}</div>
                    </div>
                  ) : (
                    /* Trick display when stepping through play */
                    <ReplayTrickDisplay
                      trick={currentReplayTrick}
                      leader={currentReplayLeader}
                    />
                  )}
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

          {/* Feedback panel - always reserve space to prevent layout shift */}
          {tricks.length > 0 && (
            <div className="trick-feedback-container">
              {replayPosition === 0 ? (
                /* Start hint - shows at position 0 */
                <div className="replay-start-hint">
                  <p>Press <strong>Next →</strong> or use arrow keys to step through each play and see feedback.</p>
                </div>
              ) : currentReplayDecision ? (
                <TrickFeedbackPanel decision={currentReplayDecision} />
              ) : (
                /* Empty state when no feedback for this position */
                <div className="trick-feedback-panel no-data">
                  <p>AI play - no feedback recorded</p>
                </div>
              )}
            </div>
          )}

          {/* Compact stats row */}
          <div className="deal-stats-consolidated">
            <div className="stat-block">
              <span className="stat-label">Result</span>
              {(() => {
                const result = getResultForUser();
                return (
                  <span className={`stat-value ${result.isGood ? 'success' : 'danger'}`}>
                    {result.text}
                    {result.detail && <> {result.detail}</>}
                  </span>
                );
              })()}
            </div>
            {handData?.par_comparison?.dd_tricks !== undefined && (
              <div className="stat-block">
                <span className="stat-label">Perfect Play</span>
                <span className="stat-value">{handData.par_comparison.dd_tricks} tricks</span>
              </div>
            )}
            {handData?.hand_score !== undefined && (
              <div className="stat-block">
                <span className="stat-label">Your Score</span>
                {(() => {
                  const userScore = getScoreForUser();
                  return (
                    <span className={`stat-value ${userScore >= 0 ? 'success' : 'danger'}`}>
                      {userScore > 0 ? '+' : ''}{userScore}
                    </span>
                  );
                })()}
              </div>
            )}
            <div className="stat-block">
              <span className="stat-label">Role</span>
              <span className="stat-value">
                {userRole}
              </span>
            </div>
          </div>

          {/* Action buttons if showing result section */}
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
        </div>
      </div>
    </div>
  );
};

export default HandReviewModal;
