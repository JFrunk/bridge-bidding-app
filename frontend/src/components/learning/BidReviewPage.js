/**
 * BidReviewPage - Full-screen bid-by-bid analysis page
 *
 * System v2.0 compliant - Uses ReactorLayout for consistent table layout.
 * Matches the HandReviewPage for consistent user mental model.
 *
 * Entry points:
 * - After bidding completion (returns to play screen)
 * - From My Progress (returns to progress)
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  SkipBack,
  SkipForward,
  ArrowLeft,
  BarChart2
} from 'lucide-react';
import { getBiddingHandDetail } from '../../services/analyticsService';
import { bidderRole, normalize, seatIndex, seatFromIndex } from '../../utils/seats';
import ReactorLayout from '../layout/ReactorLayout';
import AuctionArena from '../shared/AuctionArena';
import FeedbackDashboard from './hand-review/FeedbackDashboard';
import Card from '../../shared/components/Card';
import {
  getSuitOrder,
  normalizeSuit,
  isRedSuit,
  groupCardsBySuit,
  sortCards
} from './hand-review/constants';
import './hand-review/HandReviewPage.css';
import './BidReviewPage.css';

/**
 * ReplayHorizontalHand - Physics v2.0 compliant horizontal hand for N/S positions
 */
const ReplayHorizontalHand = ({ cards, position, scaleClass = 'text-base', isUser = false }) => {
  const suitOrder = getSuitOrder(null); // No trump for bidding
  const cardsBySuit = useMemo(() => {
    const grouped = groupCardsBySuit(cards);
    Object.keys(grouped).forEach(suit => {
      grouped[suit] = sortCards(grouped[suit]);
    });
    return grouped;
  }, [cards]);

  const getSpacingClass = (count) => {
    if (count >= 7) return '-space-x-[2.2em]';
    if (count === 6) return '-space-x-[1.9em]';
    if (count === 5) return '-space-x-[1.6em]';
    return '-space-x-[1.4em]';
  };

  const positionLabels = { N: 'North', S: 'South' };

  if (!cards || cards.length === 0) {
    return (
      <div className={`${scaleClass} text-center text-white/60 py-4`}>
        No cards
      </div>
    );
  }

  return (
    <div className={`${scaleClass} flex flex-col items-center gap-[0.3em]`}>
      <div className="text-[0.75em] font-semibold text-white/70 uppercase tracking-wider flex items-center gap-2">
        {positionLabels[position]}
        {isUser && (
          <span className="bg-blue-500 text-white px-2 py-0.5 rounded-full text-[0.7em] normal-case">
            You
          </span>
        )}
      </div>
      <div className="flex flex-row gap-[0.8em] justify-center">
        {suitOrder.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (!suitCards || suitCards.length === 0) return null;
          const spacingClass = getSpacingClass(suitCards.length);

          return (
            <div key={suit} className={`flex flex-row ${spacingClass}`}>
              {suitCards.map((card, idx) => (
                <div key={`${card.rank}-${card.suit}`} style={{ zIndex: 10 + idx }}>
                  <Card
                    rank={card.rank}
                    suit={card.suit}
                    customScaleClass={scaleClass}
                  />
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

/**
 * ReplaySuitStack - Physics v2.0 compliant vertical suit stack for E/W positions
 */
const ReplaySuitStack = ({ cards, position, scaleClass = 'text-sm' }) => {
  const suitOrder = getSuitOrder(null);
  const cardsBySuit = useMemo(() => {
    const grouped = groupCardsBySuit(cards);
    Object.keys(grouped).forEach(suit => {
      grouped[suit] = sortCards(grouped[suit]);
    });
    return grouped;
  }, [cards]);

  const getSpacingClass = (count) => {
    if (count >= 7) return '-space-x-[1.9em]';
    if (count === 6) return '-space-x-[1.6em]';
    if (count === 5) return '-space-x-[1.4em]';
    return '-space-x-[1.2em]';
  };

  const positionLabels = { E: 'East', W: 'West' };

  if (!cards || cards.length === 0) {
    return (
      <div className={`${scaleClass} text-center text-white/60 py-4`}>
        No cards
      </div>
    );
  }

  return (
    <div className={`${scaleClass} flex flex-col items-center gap-[0.3em]`}>
      <div className="text-[0.75em] font-semibold text-white/70 uppercase tracking-wider">
        {positionLabels[position]}
      </div>
      <div className="flex flex-col gap-[0.3em]">
        {suitOrder.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (!suitCards || suitCards.length === 0) return null;
          const spacingClass = getSpacingClass(suitCards.length);

          return (
            <div key={suit} className={`flex flex-row ${spacingClass}`}>
              {suitCards.map((card, idx) => (
                <div key={`${card.rank}-${card.suit}`} style={{ zIndex: 10 + idx }}>
                  <Card
                    rank={card.rank}
                    suit={card.suit}
                    customScaleClass={scaleClass}
                  />
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

/**
 * Map bid correctness to FeedbackDashboard grade
 */
const mapCorrectnessToGrade = (decision) => {
  if (!decision) return 'reasonable';

  switch (decision.correctness) {
    case 'optimal':
      return 'optimal';
    case 'acceptable':
      return 'reasonable';
    case 'suboptimal':
      return 'questionable';
    case 'error':
      return 'blunder';
    default:
      return 'reasonable';
  }
};

/**
 * Build analysis text from decision data
 */
const buildAnalysisText = (decision) => {
  if (!decision) return null;

  // Priority: reasoning > partner_communicated + you_communicated
  if (decision.reasoning) return decision.reasoning;

  const parts = [];
  if (decision.partner_communicated) {
    parts.push(`Partner showed: ${decision.partner_communicated}`);
  }
  if (decision.you_communicated) {
    parts.push(`Your message: ${decision.you_communicated}`);
  }

  if (parts.length > 0) return parts.join('. ');

  // Fallback based on correctness
  const grade = mapCorrectnessToGrade(decision);
  if (grade === 'optimal') return 'This was the best bid in this situation.';
  if (grade === 'reasonable') return 'A solid choice that keeps the bidding on track.';

  return null;
};

/**
 * Parse a bid string to card-like format for FeedbackDashboard
 * (For showing alternative bids)
 */
const parseBidToCard = (bid) => {
  if (!bid) return null;
  // Extract level and suit/NT from bid like "1NT", "2H", "3S"
  const match = bid.match(/^(\d+)(NT|[SHDC])$/i);
  if (!match) return { rank: bid, suit: '' }; // Pass, X, XX, etc.
  return { rank: match[1], suit: match[2] };
};

// Normalize position from full name to single letter
const normalizePosition = (pos) => {
  if (!pos) return 'N';
  const posMap = { 'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W' };
  return posMap[pos] || pos;
};

// Main component
const BidReviewPage = ({
  handId,
  onBack,
  onPrevHand,
  onNextHand,
  currentIndex,
  totalHands
}) => {
  const [handData, setHandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [bidPosition, setBidPosition] = useState(0);
  const [chartExpanded, setChartExpanded] = useState(false);

  // Fetch hand data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await getBiddingHandDetail(handId);
        setHandData(data);
        setBidPosition(0);
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

  const totalBids = handData?.auction_history?.length || 0;
  const userPosition = handData?.user_position || 'S';
  const allHands = handData?.all_hands || {};

  // Map decisions by bid number
  const decisionsByBidNumber = useMemo(() => {
    const map = {};
    (handData?.bidding_decisions || []).forEach(d => {
      map[d.bid_number] = d;
    });
    return map;
  }, [handData?.bidding_decisions]);

  // Get user bid numbers for highlighting
  const userBidNumbers = useMemo(() => {
    if (!handData?.auction_history || !handData?.dealer) return [];

    const positions = ['N', 'E', 'S', 'W'];
    const normalizedDealer = normalizePosition(handData.dealer);
    const dealerIndex = positions.indexOf(normalizedDealer);
    const userBids = [];

    handData.auction_history.forEach((_, idx) => {
      const positionIndex = (dealerIndex + idx) % 4;
      if (positions[positionIndex] === userPosition) {
        userBids.push(idx + 1);
      }
    });

    return userBids;
  }, [handData?.auction_history, handData?.dealer, userPosition]);

  // Get current decision for display
  const currentDecision = useMemo(() => {
    if (bidPosition === 0) return null;

    // If this is a user bid, show its analysis
    if (userBidNumbers.includes(bidPosition)) {
      return decisionsByBidNumber[bidPosition];
    }

    // Otherwise show most recent user bid analysis
    const recentUserBid = userBidNumbers
      .filter(n => n <= bidPosition)
      .sort((a, b) => b - a)[0];

    return recentUserBid ? decisionsByBidNumber[recentUserBid] : null;
  }, [bidPosition, userBidNumbers, decisionsByBidNumber]);

  // Bidding stats
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

  // Keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape' && onBack) {
      onBack();
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
  }, [bidPosition, totalBids, onBack]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Navigation handlers
  const goToStart = () => setBidPosition(0);
  const goToEnd = () => setBidPosition(totalBids);
  const goPrev = () => bidPosition > 0 && setBidPosition(p => p - 1);
  const goNext = () => bidPosition < totalBids && setBidPosition(p => p + 1);

  // Loading state
  if (loading) {
    return (
      <div className="hand-review-page">
        <div className="loading-state">Loading bidding analysis...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="hand-review-page">
        <div className="error-state">
          <p>Error: {error}</p>
          <button className="back-btn" onClick={onBack}>Go Back</button>
        </div>
      </div>
    );
  }

  // Determine if current position is a user bid
  const isUserBidPosition = userBidNumbers.includes(bidPosition);

  return (
    <div className="hand-review-page" data-testid="bid-review-page">
      {/* Stage Container - Centered flexbox column for all content */}
      <div className="stage-container">
        {/* Header Bar - Constrained to table width */}
        <div className="header-bar">
          <button className="back-btn" onClick={onBack}>
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>

          <div className="contract-summary">
            <span className="contract-badge">
              Bidding Review
            </span>
            {handData?.contract && (
              <>
                <span className="contract-by">Final:</span>
                <span className={`contract-badge ${isRedSuit(handData.contract.match(/[SHDC\u2660\u2665\u2666\u2663]/i)?.[0]) ? 'red' : ''}`}>
                  {handData.contract}
                </span>
              </>
            )}
            {biddingStats && (
              <>
                <span className="accuracy-badge">{biddingStats.optimalRate}% optimal</span>
                <span className="score-badge positive">{biddingStats.avgScore}/10</span>
              </>
            )}
          </div>

          <button
            className={`chart-toggle ${chartExpanded ? 'active' : ''}`}
            onClick={() => setChartExpanded(!chartExpanded)}
            title="Toggle DD table"
          >
            <BarChart2 size={18} />
          </button>
        </div>

        {/* ReactorLayout - System v2.0 compliant table layout */}
        <ReactorLayout
          className="replay-reactor"
          scaleClass="text-base"
          north={
            <ReplayHorizontalHand
              cards={allHands.N?.cards || []}
              position="N"
              scaleClass="text-lg"
              isUser={userPosition === 'N'}
            />
          }
          south={
            <ReplayHorizontalHand
              cards={allHands.S?.cards || []}
              position="S"
              scaleClass="text-xl"
              isUser={userPosition === 'S'}
            />
          }
          east={
            <ReplaySuitStack
              cards={allHands.E?.cards || []}
              position="E"
              scaleClass="text-sm"
            />
          }
          west={
            <ReplaySuitStack
              cards={allHands.W?.cards || []}
              position="W"
              scaleClass="text-sm"
            />
          }
          center={
            <AuctionArena
              auctionHistory={handData?.auction_history || []}
              dealer={handData?.dealer || 'N'}
              currentPosition={bidPosition}
              userPosition={userPosition}
              scaleClass="text-base"
            />
          }
        />

        {/* Pit Container - Footer controls constrained to table width */}
        <div className="pit-container">
          {/* Replay Navigation Controls - Always visible */}
          <div className="replay-controls">
            <button className="replay-btn icon-only" onClick={goToStart} disabled={bidPosition <= 0} title="Start (Home)">
              <SkipBack size={18} />
            </button>
            <button className="replay-btn prev" onClick={goPrev} disabled={bidPosition <= 0}>
              <ChevronLeft size={18} />
              <span>Prev</span>
            </button>
            <span className="replay-counter">
              {bidPosition === 0 ? 'Start' : `Bid ${bidPosition} of ${totalBids}`}
              {isUserBidPosition && <span className="text-blue-400 ml-1">(Your bid)</span>}
            </span>
            <button className="replay-btn next primary" onClick={goNext} disabled={bidPosition >= totalBids} data-testid="nav-next">
              <span>Next</span>
              <ChevronRight size={18} />
            </button>
            <button className="replay-btn icon-only" onClick={goToEnd} disabled={bidPosition >= totalBids} title="End (End)">
              <SkipForward size={18} />
            </button>

            {/* Hand navigation (when multiple hands) */}
            {totalHands > 1 && (
              <div className="hand-nav">
                <button className="replay-btn small" onClick={onPrevHand} disabled={!onPrevHand}>
                  <ChevronLeft size={14} />
                </button>
                <span className="hand-counter">{currentIndex + 1}/{totalHands}</span>
                <button className="replay-btn small" onClick={onNextHand} disabled={!onNextHand}>
                  <ChevronRight size={14} />
                </button>
              </div>
            )}
          </div>

          {/* Feedback Dashboard - Learning Coach */}
          {totalBids > 0 && (
            <FeedbackDashboard
              grade={currentDecision ? mapCorrectnessToGrade(currentDecision) : 'reasonable'}
              analysisText={buildAnalysisText(currentDecision)}
              alternativePlay={
                currentDecision?.optimal_bid &&
                currentDecision.optimal_bid !== currentDecision.user_bid
                  ? parseBidToCard(currentDecision.optimal_bid)
                  : null
              }
              playedCard={currentDecision?.user_bid ? parseBidToCard(currentDecision.user_bid) : null}
              tricksCost={0} // Bidding doesn't have trick cost
              isStart={bidPosition === 0}
              isAiPlay={!isUserBidPosition && bidPosition > 0 && !currentDecision}
            />
          )}

          {/* DD Table (Collapsible) */}
          {handData?.dd_analysis?.dd_table && chartExpanded && (
            <div className="chart-panel expanded">
              <DDTableDisplay ddAnalysis={handData.dd_analysis} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// DD Table Display Component
const DDTableDisplay = ({ ddAnalysis }) => {
  if (!ddAnalysis?.dd_table) return null;

  const strains = ['NT', 'S', 'H', 'D', 'C'];
  const strainSymbols = { NT: 'NT', S: '\u2660', H: '\u2665', D: '\u2666', C: '\u2663' };
  const positions = ['N', 'S', 'E', 'W'];

  const getContractLevel = (tricks, strain) => {
    if (typeof tricks !== 'number') return 'partscore';
    if (tricks >= 13) return 'grand';
    if (tricks >= 12) return 'slam';

    const isMinor = strain === 'C' || strain === 'D';
    const isMajor = strain === 'S' || strain === 'H';

    if (strain === 'NT' && tricks >= 9) return 'game';
    if (isMajor && tricks >= 10) return 'game';
    if (isMinor && tricks >= 11) return 'game';

    return 'partscore';
  };

  return (
    <div className="bg-white rounded-lg p-4 w-full">
      <h4 className="text-sm font-semibold text-gray-700 mb-3">Possible Tricks (Double Dummy)</h4>
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="text-left p-1"></th>
            {strains.map(strain => (
              <th
                key={strain}
                className={`text-center p-1 font-bold ${
                  strain === 'H' || strain === 'D' ? 'text-red-600' : 'text-gray-800'
                }`}
              >
                {strainSymbols[strain]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map(pos => (
            <tr key={pos}>
              <th className="text-left p-1 font-semibold text-gray-600">{pos}</th>
              {strains.map(strain => {
                const tricks = ddAnalysis.dd_table[pos]?.[strain] ?? '-';
                const level = getContractLevel(tricks, strain);
                const bgClass = level === 'game' ? 'bg-blue-100' :
                               level === 'slam' ? 'bg-purple-100' :
                               level === 'grand' ? 'bg-yellow-100' : '';
                return (
                  <td key={strain} className={`text-center p-1 ${bgClass}`}>
                    {tricks}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {ddAnalysis.par && (
        <div className="mt-3 pt-3 border-t border-gray-200 text-sm">
          <span className="font-medium text-gray-600">Par: </span>
          <span className="font-semibold">
            {ddAnalysis.par.contracts?.join(' / ') || 'Unknown'}
            {ddAnalysis.par.score !== undefined && ` (${ddAnalysis.par.score >= 0 ? '+' : ''}${ddAnalysis.par.score})`}
          </span>
        </div>
      )}
    </div>
  );
};

export default BidReviewPage;
