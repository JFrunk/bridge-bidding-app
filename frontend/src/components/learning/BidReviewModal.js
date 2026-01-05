/**
 * BidReviewModal Component - Unified bid-by-bid analysis
 *
 * Reuses the same interface pattern as HandReviewModal (play-by-play):
 * 1. Shows all 4 hands in compass layout
 * 2. Navigation controls at top (Prev/Next with arrow keys)
 * 3. Center area shows auction building up progressively
 * 4. Feedback panel below shows analysis for current user bid
 *
 * Design Philosophy:
 * - Consistent with play-by-play for user familiarity
 * - Single pane, single interaction pattern
 * - Start at position 0 showing all dealt hands with empty auction
 * - Use arrow keys or buttons to step through bid-by-bid
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { PlayableCard } from '../play/PlayableCard';
import { getBiddingHandDetail } from '../../services/analyticsService';
import ChartHelp from '../help/ChartHelp';
import './HandReviewModal.css'; // Reuse the same CSS

// Rating colors and labels (same as HandReviewModal)
const RATING_CONFIG = {
  optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '✓', label: 'Optimal' },
  acceptable: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Acceptable' },
  suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
  error: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Error' }
};

// Suit order for display
const SUIT_ORDER = ['♠', '♥', '♦', '♣'];

// Normalize suit to Unicode format
const normalizeSuit = (suit) => {
  const map = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
  return map[suit] || suit;
};

// Sort cards within a suit by rank (high to low)
const sortCards = (cards) => {
  const rankOrder = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
  return [...cards].sort((a, b) => {
    const aRank = a.rank || a.r;
    const bRank = b.rank || b.r;
    return rankOrder.indexOf(aRank) - rankOrder.indexOf(bRank);
  });
};

// Hand display component - reuses replay-hand styling from HandReviewModal
const BidHandDisplay = ({ cards, position, isVertical = false }) => {
  const cardsBySuit = useMemo(() => {
    const grouped = { '♠': [], '♥': [], '♦': [], '♣': [] };
    (cards || []).forEach(card => {
      const suit = normalizeSuit(card.suit || card.s);
      if (grouped[suit]) {
        grouped[suit].push({
          rank: card.rank || card.r,
          suit: suit
        });
      }
    });
    Object.keys(grouped).forEach(suit => {
      grouped[suit] = sortCards(grouped[suit]);
    });
    return grouped;
  }, [cards]);

  const positionLabels = { N: 'NORTH', E: 'EAST', S: 'SOUTH', W: 'WEST' };

  // Vertical 2-column layout for E/W
  if (isVertical) {
    const col1Suits = SUIT_ORDER.filter(s => s === '♠' || s === '♥');
    const col2Suits = SUIT_ORDER.filter(s => s === '♦' || s === '♣');

    return (
      <div className={`replay-hand replay-hand-${position.toLowerCase()} vertical-2col`}>
        <div className="replay-hand-label">{positionLabels[position]}</div>
        <div className="replay-hand-2col">
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
        {(!cards || cards.length === 0) && (
          <div className="replay-hand-empty">No cards</div>
        )}
      </div>
    );
  }

  // Horizontal layout for N/S
  return (
    <div className={`replay-hand replay-hand-${position.toLowerCase()} horizontal`}>
      <div className="replay-hand-label">{positionLabels[position]}</div>
      <div className="replay-hand-cards">
        {SUIT_ORDER.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (suitCards.length === 0) return null;
          return (
            <div key={suit} className="replay-suit-group">
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
        {(!cards || cards.length === 0) && (
          <div className="replay-hand-empty">No cards</div>
        )}
      </div>
    </div>
  );
};

// Position order constant
const POSITIONS = ['N', 'E', 'S', 'W'];

// Center auction display - shows bids up to current position
const AuctionCenterDisplay = ({ auctionHistory, dealer, currentPosition, userPosition }) => {
  const dealerIndex = POSITIONS.indexOf(dealer || 'N');

  // Build auction rows showing only bids up to currentPosition
  const rows = useMemo(() => {
    if (!auctionHistory || auctionHistory.length === 0 || currentPosition === 0) {
      return [];
    }

    const visibleBids = auctionHistory.slice(0, currentPosition);
    const result = [];
    let currentRow = new Array(4).fill(null);

    // Add empty cells before dealer
    for (let i = 0; i < dealerIndex; i++) {
      currentRow[i] = { empty: true };
    }

    let colIndex = dealerIndex;

    visibleBids.forEach((bidInfo) => {
      const bid = typeof bidInfo === 'string' ? bidInfo : bidInfo.bid;
      const position = POSITIONS[colIndex];
      const isUserBid = position === userPosition;

      currentRow[colIndex] = {
        bid,
        position,
        isUserBid
      };

      colIndex++;
      if (colIndex >= 4) {
        result.push([...currentRow]);
        currentRow = new Array(4).fill(null);
        colIndex = 0;
      }
    });

    // Add final incomplete row if needed
    if (currentRow.some(c => c !== null)) {
      result.push(currentRow);
    }

    return result;
  }, [auctionHistory, dealerIndex, currentPosition, userPosition]);

  // At position 0, show deal info
  if (currentPosition === 0) {
    return (
      <div className="center-info-box">
        <div className="center-contract">Bidding Review</div>
        <div className="center-vulnerability">Dealer: {dealer || 'N'}</div>
        <div className="center-dealer">Step through to see each bid</div>
      </div>
    );
  }

  return (
    <div className="bid-auction-center">
      <div className="bid-auction-header">
        {POSITIONS.map(pos => (
          <div
            key={pos}
            className={`bid-auction-col ${pos === userPosition ? 'user-col' : ''}`}
          >
            {pos}
          </div>
        ))}
      </div>
      <div className="bid-auction-body">
        {rows.map((row, rowIdx) => (
          <div key={rowIdx} className="bid-auction-row">
            {row.map((cell, colIdx) => (
              <div
                key={colIdx}
                className={`bid-auction-cell ${cell?.isUserBid ? 'user-bid' : ''} ${cell?.empty ? 'empty' : ''}`}
              >
                {cell?.empty ? '' : cell?.bid || ''}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

// Bid feedback panel - shows analysis for current user bid
const BidFeedbackPanel = ({ decision }) => {
  if (!decision) {
    return (
      <div className="trick-feedback-panel no-data">
        <p>No analysis available for this bid</p>
      </div>
    );
  }

  const config = RATING_CONFIG[decision.correctness] || RATING_CONFIG.acceptable;
  const isCorrect = decision.user_bid === decision.optimal_bid;

  return (
    <div
      className={`trick-feedback-panel ${decision.correctness}`}
      style={{ borderColor: config.color, backgroundColor: config.bgColor }}
    >
      <div className="feedback-header">
        <span className="feedback-badge" style={{ backgroundColor: config.color }}>
          {config.icon} {config.label}
        </span>
        <span className="bid-score">{decision.score}/10</span>
      </div>

      <div className="feedback-body">
        <div className="play-comparison">
          <span className="played-card">
            <strong>Your bid:</strong> {decision.user_bid}
          </span>
          {!isCorrect && decision.optimal_bid && (
            <span className="optimal-card">
              <strong>Better:</strong> {decision.optimal_bid}
            </span>
          )}
        </div>

        {decision.partner_communicated && (
          <p className="feedback-text" style={{ borderTop: 'none', paddingTop: 0 }}>
            <strong>Partner:</strong> {decision.partner_communicated}
          </p>
        )}

        {decision.you_communicated && (
          <p className="feedback-text" style={{ borderTop: 'none', paddingTop: 0 }}>
            <strong>Your message:</strong> {decision.you_communicated}
          </p>
        )}

        {decision.reasoning && (
          <p className="feedback-text">{decision.reasoning}</p>
        )}
      </div>
    </div>
  );
};

// Main modal component
const BidReviewModal = ({ handId, onClose }) => {
  const [handData, setHandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [bidPosition, setBidPosition] = useState(0); // 0 to totalBids

  // Fetch bidding hand details
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await getBiddingHandDetail(handId);
        setHandData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (handId) {
      fetchData();
    }
  }, [handId]);

  // Total bids for navigation
  const totalBids = handData?.auction_history?.length || 0;

  // Get user position
  const userPosition = handData?.user_position || 'S';

  // Build decision lookup by bid number in auction
  const decisionsByBidNumber = useMemo(() => {
    const map = {};
    (handData?.bidding_decisions || []).forEach(d => {
      map[d.bid_number] = d;
    });
    return map;
  }, [handData?.bidding_decisions]);

  // Find which bid numbers are user bids
  const userBidNumbers = useMemo(() => {
    if (!handData?.auction_history || !handData?.dealer) return [];

    const positions = ['N', 'E', 'S', 'W'];
    const dealerIndex = positions.indexOf(handData.dealer);
    const userBids = [];

    handData.auction_history.forEach((_, idx) => {
      const positionIndex = (dealerIndex + idx) % 4;
      if (positions[positionIndex] === userPosition) {
        userBids.push(idx + 1); // 1-indexed
      }
    });

    return userBids;
  }, [handData?.auction_history, handData?.dealer, userPosition]);

  // Get decision for current bid if it's a user bid
  const currentDecision = useMemo(() => {
    if (bidPosition === 0) return null;

    // Check if current bid position is a user bid
    if (userBidNumbers.includes(bidPosition)) {
      return decisionsByBidNumber[bidPosition];
    }

    // Find the most recent user bid before current position
    const recentUserBid = userBidNumbers
      .filter(n => n <= bidPosition)
      .sort((a, b) => b - a)[0];

    return recentUserBid ? decisionsByBidNumber[recentUserBid] : null;
  }, [bidPosition, userBidNumbers, decisionsByBidNumber]);

  // Get all hands data
  const allHands = handData?.all_hands || {};

  // Navigate with keyboard
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }

    if (e.key === 'ArrowLeft' && bidPosition > 0) {
      setBidPosition(p => p - 1);
    } else if (e.key === 'ArrowRight' && bidPosition < totalBids) {
      setBidPosition(p => p + 1);
    } else if (e.key === 'Home') {
      setBidPosition(0);
    } else if (e.key === 'End') {
      setBidPosition(totalBids);
    }
  }, [bidPosition, totalBids, onClose]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Calculate bidding quality stats
  const biddingStats = useMemo(() => {
    const decisions = handData?.bidding_decisions || [];
    if (decisions.length === 0) return null;

    const avgScore = decisions.reduce((sum, d) => sum + (d.score || 0), 0) / decisions.length;
    const optimalCount = decisions.filter(d => d.correctness === 'optimal').length;

    return {
      avgScore: Math.round(avgScore * 10) / 10,
      optimalRate: Math.round((optimalCount / decisions.length) * 100),
      totalDecisions: decisions.length
    };
  }, [handData?.bidding_decisions]);

  if (loading) {
    return (
      <div className="hand-review-modal-overlay" onClick={onClose}>
        <div className="hand-review-modal" onClick={e => e.stopPropagation()}>
          <div className="loading-state">Loading bidding analysis...</div>
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
        {/* Header with contract info */}
        <div className="modal-header">
          <div className="modal-title">
            <div className="modal-title-row">
              <h2>Bidding Review</h2>
              <ChartHelp chartType="bidding-review" variant="icon" />
            </div>
            <div className="contract-info">
              {handData?.contract && (
                <span className="contract">
                  Final: {handData.contract}
                </span>
              )}
              {biddingStats && (
                <>
                  <span className="accuracy-badge bidding">{biddingStats.optimalRate}% optimal</span>
                  <span className="accuracy-badge">{biddingStats.avgScore}/10 avg</span>
                </>
              )}
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {/* Content */}
        <div className="modal-content unified-container">
          {/* Navigation controls */}
          {totalBids > 0 && (
            <div className="replay-navigation">
              <button
                disabled={bidPosition <= 0}
                onClick={() => setBidPosition(0)}
                aria-label="Go to start"
                title="Go to start (Home)"
              >
                ⏮
              </button>
              <button
                disabled={bidPosition <= 0}
                onClick={() => setBidPosition(p => p - 1)}
                aria-label="Previous bid"
              >
                ← Prev
              </button>
              <span className="replay-counter">
                {bidPosition === 0 ? (
                  'Start • All hands dealt'
                ) : (
                  <>
                    Bid {bidPosition} of {totalBids}
                    {userBidNumbers.includes(bidPosition) && (
                      <span className="trick-indicator"> (Your bid)</span>
                    )}
                  </>
                )}
              </span>
              <button
                disabled={bidPosition >= totalBids}
                onClick={() => setBidPosition(p => p + 1)}
                aria-label="Next bid"
              >
                Next →
              </button>
              <button
                disabled={bidPosition >= totalBids}
                onClick={() => setBidPosition(totalBids)}
                aria-label="Go to end"
                title="Go to end (End)"
              >
                ⏭
              </button>
            </div>
          )}

          {/* Compass layout with all 4 hands */}
          <div className="replay-table-compass">
            {/* North hand */}
            <div className="replay-row replay-row-north">
              <div className="replay-position">
                <BidHandDisplay
                  cards={allHands.N?.cards || []}
                  position="N"
                  isVertical={false}
                />
              </div>
            </div>

            {/* Middle row: West - Auction - East */}
            <div className="replay-row replay-row-middle">
              <div className="replay-position replay-west">
                <BidHandDisplay
                  cards={allHands.W?.cards || []}
                  position="W"
                  isVertical={true}
                />
              </div>

              <div className="replay-center">
                <AuctionCenterDisplay
                  auctionHistory={handData?.auction_history || []}
                  dealer={handData?.dealer}
                  currentPosition={bidPosition}
                  userPosition={userPosition}
                />
              </div>

              <div className="replay-position replay-east">
                <BidHandDisplay
                  cards={allHands.E?.cards || []}
                  position="E"
                  isVertical={true}
                />
              </div>
            </div>

            {/* South hand */}
            <div className="replay-row replay-row-south">
              <div className="replay-position">
                <BidHandDisplay
                  cards={allHands.S?.cards || []}
                  position="S"
                  isVertical={false}
                />
              </div>
            </div>
          </div>

          {/* Feedback panel */}
          {totalBids > 0 && (
            <div className="trick-feedback-container">
              {bidPosition === 0 ? (
                <div className="replay-start-hint">
                  <p>Press <strong>Next →</strong> or use arrow keys to step through each bid and see feedback.</p>
                </div>
              ) : currentDecision ? (
                <BidFeedbackPanel decision={currentDecision} />
              ) : (
                <div className="trick-feedback-panel no-data">
                  {userBidNumbers.includes(bidPosition) ? (
                    <p>Your bid - no analysis recorded</p>
                  ) : (
                    <p>{(() => {
                      // Determine who made this bid
                      const positions = ['N', 'E', 'S', 'W'];
                      const dealerIndex = positions.indexOf(handData?.dealer || 'N');
                      const bidderPos = positions[(dealerIndex + bidPosition - 1) % 4];
                      const bidderName = bidderPos === 'N' ? 'North (Partner)' : bidderPos === 'E' ? 'East (Opponent)' : bidderPos === 'W' ? 'West (Opponent)' : 'South (You)';
                      return `${bidderName} bid - no analysis recorded`;
                    })()}</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Stats row */}
          <div className="deal-stats-consolidated">
            {handData?.contract && (
              <div className="stat-block">
                <span className="stat-label">Contract</span>
                <span className="stat-value">{handData.contract}</span>
              </div>
            )}
            {biddingStats && (
              <>
                <div className="stat-block">
                  <span className="stat-label">Your Bids</span>
                  <span className="stat-value">{biddingStats.totalDecisions}</span>
                </div>
                <div className="stat-block">
                  <span className="stat-label">Optimal Rate</span>
                  <span className={`stat-value ${biddingStats.optimalRate >= 70 ? 'success' : ''}`}>
                    {biddingStats.optimalRate}%
                  </span>
                </div>
              </>
            )}
            <div className="stat-block">
              <span className="stat-label">Position</span>
              <span className="stat-value">{userPosition}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BidReviewModal;
