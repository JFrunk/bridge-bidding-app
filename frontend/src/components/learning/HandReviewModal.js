/**
 * HandReviewModal Component - Unified hand analysis with accordion layout
 *
 * Features:
 * - Single scrollable view with expandable sections (accordion)
 * - STRATEGY: Overview of the deal with hand display
 * - YOUR PLAY: Performance summary with accuracy stats
 * - PERFECT PLAY: What optimal play would achieve (replaces "Double Dummy")
 * - PLAY-BY-PLAY: Interactive card-by-card replay with feedback
 *
 * Design Philosophy:
 * - Unified accordion UI eliminates confusing mode toggles
 * - Collapsed sections show summary previews
 * - Mobile: one section at a time; Desktop: allow multiple
 * - "Perfect Play" terminology replaces jargon like "Double Dummy"
 *
 * Requires hand_id to be passed as prop.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PlayableCard } from '../play/PlayableCard';
import './HandReviewModal.css';

// ===== ACCORDION SECTION COMPONENT =====
// Reusable accordion section following existing design patterns from LearningDashboard
const AccordionSection = ({
  id,
  title,
  subtitle,
  icon,
  isOpen,
  onToggle,
  summary,
  children
}) => {
  return (
    <div className={`accordion-section ${isOpen ? 'open' : ''}`}>
      <button
        className="accordion-header"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-controls={`accordion-content-${id}`}
      >
        <div className="accordion-title-group">
          {icon && <span className="accordion-icon">{icon}</span>}
          <div className="accordion-titles">
            <span className="accordion-title">{title}</span>
            {subtitle && <span className="accordion-subtitle">{subtitle}</span>}
          </div>
        </div>
        <div className="accordion-right">
          {!isOpen && summary && (
            <span className="accordion-summary">{summary}</span>
          )}
          <span className={`accordion-toggle-icon ${isOpen ? 'open' : ''}`}>▼</span>
        </div>
      </button>
      <div
        id={`accordion-content-${id}`}
        className={`accordion-content ${isOpen ? 'open' : ''}`}
        aria-hidden={!isOpen}
      >
        {isOpen && children}
      </div>
    </div>
  );
};

const API_BASE = process.env.REACT_APP_API_BASE || '';

// Rating colors and labels
const RATING_CONFIG = {
  optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '✓', label: 'Optimal' },
  good: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Good' },
  suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
  blunder: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Blunder' }
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

      {/* Mistakes warning - show count of plays that cost tricks */}
      {(summary.suboptimal_count + summary.blunder_count) > 0 && (
        <div className="tricks-lost-warning">
          <span className="warning-icon">!</span>
          {summary.suboptimal_count + summary.blunder_count} play{(summary.suboptimal_count + summary.blunder_count) !== 1 ? 's' : ''} could be improved
        </div>
      )}
    </div>
  );
};

// DD Table display - shows tricks makeable by each player in each strain
// Note: "Perfect Play" terminology replaces "Double Dummy" for user clarity
const DDTableDisplay = ({ ddAnalysis, contractStrain, contractDeclarer }) => {
  if (!ddAnalysis?.dd_table) {
    return null;
  }

  const strains = ['NT', 'S', 'H', 'D', 'C'];
  const strainSymbols = { 'NT': 'NT', 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
  const strainColors = { 'NT': '#374151', 'S': '#000', 'H': '#dc2626', 'D': '#dc2626', 'C': '#000' };
  const positions = ['N', 'S', 'E', 'W'];

  // Normalize contract strain for comparison
  const normalizeStrain = (s) => {
    const map = { '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' };
    return map[s] || s;
  };
  const activeStrain = normalizeStrain(contractStrain);

  return (
    <div className="dd-table-display">
      <h4>Perfect Play Analysis</h4>
      <p className="dd-table-subtitle">Tricks achievable with optimal play by all</p>
      <table className="dd-table">
        <thead>
          <tr>
            <th></th>
            {strains.map(strain => (
              <th
                key={strain}
                className={strain === activeStrain ? 'active-strain' : ''}
                style={{ color: strainColors[strain] }}
              >
                {strainSymbols[strain]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map(pos => (
            <tr key={pos} className={pos === contractDeclarer ? 'active-declarer' : ''}>
              <td className="position-cell">{pos}</td>
              {strains.map(strain => {
                const tricks = ddAnalysis.dd_table[pos]?.[strain] ?? '-';
                const isActive = strain === activeStrain && pos === contractDeclarer;
                return (
                  <td
                    key={strain}
                    className={isActive ? 'active-cell' : ''}
                  >
                    {tricks}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Strategy Summary display - shows high-level strategic guidance for the hand
const StrategySummaryDisplay = ({ strategy }) => {
  if (!strategy || strategy.error) {
    return null;
  }

  const suitColors = { '♠': '#000', '♥': '#dc2626', '♦': '#dc2626', '♣': '#000' };

  return (
    <div className="strategy-summary-display">
      <h4>Hand Strategy</h4>
      <p className="strategy-main-summary">{strategy.summary}</p>

      {/* NT-specific details */}
      {strategy.is_nt && (
        <div className="strategy-details">
          <div className="strategy-stat">
            <span className="stat-label">Sure Tricks:</span>
            <span className="stat-value">{strategy.sure_tricks}</span>
          </div>
          <div className="strategy-stat">
            <span className="stat-label">Tricks Needed:</span>
            <span className="stat-value">{strategy.tricks_needed}</span>
          </div>
          {strategy.tricks_to_develop > 0 && (
            <div className="strategy-stat">
              <span className="stat-label">To Develop:</span>
              <span className="stat-value highlight">{strategy.tricks_to_develop}</span>
            </div>
          )}
          {strategy.establishment_candidates?.length > 0 && (
            <div className="establishment-candidates">
              <span className="candidates-label">Best suits to develop:</span>
              <div className="candidates-list">
                {strategy.establishment_candidates.map((c, idx) => (
                  <span key={idx} className="candidate-suit" style={{ color: suitColors[c.suit] }}>
                    {c.suit} ({c.length} cards)
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Suit contract details */}
      {!strategy.is_nt && (
        <div className="strategy-details">
          <div className="strategy-stat">
            <span className="stat-label">Losers:</span>
            <span className="stat-value">{strategy.total_losers}</span>
          </div>
          <div className="strategy-stat">
            <span className="stat-label">Can Afford:</span>
            <span className="stat-value">{strategy.losers_allowed}</span>
          </div>
          {strategy.losers_to_eliminate > 0 && (
            <div className="strategy-stat">
              <span className="stat-label">Must Eliminate:</span>
              <span className="stat-value highlight">{strategy.losers_to_eliminate}</span>
            </div>
          )}
          {strategy.ruffing_opportunities?.length > 0 && (
            <div className="ruffing-opportunities">
              <span className="ruff-label">Ruffing opportunities:</span>
              <div className="ruff-list">
                {strategy.ruffing_opportunities.map((r, idx) => (
                  <span key={idx} className="ruff-suit" style={{ color: suitColors[r.suit] }}>
                    {r.suit} ({r.ruffs_possible} ruff{r.ruffs_possible !== 1 ? 's' : ''})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Par comparison display - shows how result compares to optimal bidding
// Uses "Perfect Play" terminology instead of "DD" or "Double Dummy"
const ParComparisonDisplay = ({ ddAnalysis, parComparison, tricksNeeded, tricksTaken }) => {
  if (!ddAnalysis?.par || !parComparison?.available) {
    return null;
  }

  const { par } = ddAnalysis;
  const { dd_tricks, optimal_play, score_difference } = parComparison;

  // Determine result quality
  const getResultQuality = () => {
    if (optimal_play && tricksTaken >= tricksNeeded) {
      return { label: 'Perfect', color: '#059669', icon: '✓' };
    }
    if (tricksTaken >= dd_tricks) {
      return { label: 'Good', color: '#3b82f6', icon: '○' };
    }
    if (tricksTaken >= tricksNeeded) {
      return { label: 'Made', color: '#059669', icon: '✓' };
    }
    return { label: 'Could improve', color: '#f59e0b', icon: '!' };
  };

  const quality = getResultQuality();

  return (
    <div className="par-comparison-display">
      <h4>Contract Analysis</h4>

      <div className="par-stats">
        {/* Perfect Play Expected */}
        <div className="par-stat">
          <span className="par-stat-label">Perfect Play</span>
          <span className="par-stat-value">{dd_tricks} tricks</span>
        </div>

        {/* Actual result */}
        <div className="par-stat">
          <span className="par-stat-label">You made</span>
          <span className="par-stat-value">{tricksTaken} tricks</span>
        </div>

        {/* Play quality */}
        <div className="par-stat">
          <span className="par-stat-label">Play</span>
          <span className="par-stat-value" style={{ color: quality.color }}>
            {quality.icon} {quality.label}
          </span>
        </div>
      </div>

      {/* Par score info */}
      <div className="par-score-info">
        <div className="par-contracts">
          <span className="par-label">Par:</span>
          <span className="par-value">{par.contracts?.join(' or ') || 'Pass'}</span>
          <span className="par-score">({par.score > 0 ? '+' : ''}{par.score})</span>
        </div>

        {score_difference !== undefined && score_difference !== 0 && (
          <div className={`score-impact ${score_difference > 0 ? 'positive' : 'negative'}`}>
            {score_difference > 0 ? '+' : ''}{score_difference} vs par
          </div>
        )}
      </div>
    </div>
  );
};

const HandReviewModal = ({ handId, onClose }) => {
  const [handData, setHandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [replayPosition, setReplayPosition] = useState(0); // 0 to 52 (each card played)

  // Accordion state - track which sections are open
  // Default: Strategy section open on load
  const [openSections, setOpenSections] = useState({
    strategy: true,
    yourPlay: false,
    perfectPlay: false,
    playByPlay: false
  });

  // Toggle accordion section - on mobile, close others when opening one
  const toggleSection = useCallback((sectionId) => {
    setOpenSections(prev => {
      // Check if we're on mobile (< 768px)
      const isMobile = window.innerWidth < 768;

      if (isMobile) {
        // Mobile: only one section open at a time
        const newState = {
          strategy: false,
          yourPlay: false,
          perfectPlay: false,
          playByPlay: false
        };
        // Toggle the clicked section (if it was open, close it; otherwise open it)
        newState[sectionId] = !prev[sectionId];
        return newState;
      } else {
        // Desktop: allow multiple sections open
        return { ...prev, [sectionId]: !prev[sectionId] };
      }
    });
  }, []);

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

  // Navigate with keyboard - works when Play-by-Play section is open
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }

    // When Play-by-Play section is open, arrow keys navigate the replay
    if (openSections.playByPlay) {
      if (e.key === 'ArrowLeft' && replayPosition > 0) {
        setReplayPosition(p => p - 1);
      } else if (e.key === 'ArrowRight' && replayPosition < totalPlays) {
        setReplayPosition(p => p + 1);
      } else if (e.key === 'Home') {
        setReplayPosition(0);
      } else if (e.key === 'End') {
        setReplayPosition(totalPlays);
      }
    }
  }, [openSections.playByPlay, replayPosition, totalPlays, onClose]);

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

  // Generate summary text for collapsed accordion sections
  const getStrategySummary = () => {
    if (handData?.strategy_summary?.summary) {
      // Truncate to ~50 chars for preview
      const full = handData.strategy_summary.summary;
      return full.length > 50 ? full.substring(0, 47) + '...' : full;
    }
    return 'View deal and strategy';
  };

  const getYourPlaySummary = () => {
    const summary = handData?.play_quality_summary;
    if (summary?.has_data) {
      return `${summary.accuracy_rate}% accuracy`;
    }
    return 'View your performance';
  };

  const getPerfectPlaySummary = () => {
    if (handData?.dd_analysis?.dd_table) {
      const ddTricks = handData?.par_comparison?.dd_tricks;
      return ddTricks ? `${ddTricks} tricks achievable` : 'View optimal analysis';
    }
    return 'View optimal analysis';
  };

  const getPlayByPlaySummary = () => {
    if (totalPlays > 0) {
      return `${totalTricks} tricks to review`;
    }
    return 'Step through each play';
  };

  return (
    <div className="hand-review-modal-overlay" onClick={onClose}>
      <div className="hand-review-modal accordion-layout" onClick={e => e.stopPropagation()}>
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

        {/* Accordion Content */}
        <div className="modal-content accordion-container">

          {/* SECTION 1: STRATEGY - Deal overview and strategic guidance */}
          <AccordionSection
            id="strategy"
            title="Strategy"
            subtitle="Deal overview and plan"
            icon="🎯"
            isOpen={openSections.strategy}
            onToggle={() => toggleSection('strategy')}
            summary={getStrategySummary()}
          >
            {/* Deal display - 4 hands in text format */}
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

            {/* Strategy Summary - high-level guidance */}
            {handData?.strategy_summary && (
              <StrategySummaryDisplay strategy={handData.strategy_summary} />
            )}
          </AccordionSection>

          {/* SECTION 2: YOUR PLAY - Performance summary */}
          <AccordionSection
            id="yourPlay"
            title="Your Play"
            subtitle="Performance summary"
            icon="📊"
            isOpen={openSections.yourPlay}
            onToggle={() => toggleSection('yourPlay')}
            summary={getYourPlaySummary()}
          >
            <PlayQualitySummary summary={handData?.play_quality_summary} />
          </AccordionSection>

          {/* SECTION 3: PERFECT PLAY - DD analysis */}
          {handData?.dd_analysis && (
            <AccordionSection
              id="perfectPlay"
              title="Perfect Play"
              subtitle="Optimal analysis"
              icon="✨"
              isOpen={openSections.perfectPlay}
              onToggle={() => toggleSection('perfectPlay')}
              summary={getPerfectPlaySummary()}
            >
              <div className="dd-analysis-section">
                <DDTableDisplay
                  ddAnalysis={handData.dd_analysis}
                  contractStrain={handData.contract_strain}
                  contractDeclarer={handData.contract_declarer}
                />
                <ParComparisonDisplay
                  ddAnalysis={handData.dd_analysis}
                  parComparison={handData.par_comparison}
                  tricksNeeded={handData.tricks_needed}
                  tricksTaken={handData.tricks_taken}
                />
              </div>
            </AccordionSection>
          )}

          {/* SECTION 4: PLAY-BY-PLAY - Interactive replay */}
          {tricks.length > 0 && (
            <AccordionSection
              id="playByPlay"
              title="Play-by-Play"
              subtitle="Card-by-card replay"
              icon="🎬"
              isOpen={openSections.playByPlay}
              onToggle={() => toggleSection('playByPlay')}
              summary={getPlayByPlaySummary()}
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

                <p className="navigation-hint">Use ← → keys to step through plays</p>
              </div>
            </AccordionSection>
          )}
        </div>
      </div>
    </div>
  );
};

export default HandReviewModal;
