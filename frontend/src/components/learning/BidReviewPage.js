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
import ReactorLayout from '../layout/ReactorLayout';
import AuctionArena from '../shared/AuctionArena';
import FeedbackDashboard from './hand-review/FeedbackDashboard';
import DDTableDisplay from '../analysis/DDTableDisplay';
import { ReplayHorizontalHand, ReplaySuitStack } from './hand-review/ReplayHand';
import { isRedSuit } from './hand-review/constants';
import './hand-review/HandReviewPage.css';
import './BidReviewPage.css';

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

/**
 * Get the position (N/E/S/W) for a given bid number in the auction
 * @param {number} bidNumber - 1-indexed bid number
 * @param {string} dealer - Dealer position
 * @returns {string} Position letter (N/E/S/W)
 */
const getPositionForBidNumber = (bidNumber, dealer) => {
  const positions = ['N', 'E', 'S', 'W'];
  const normalizedDealer = normalizePosition(dealer || 'N');
  const dealerIndex = positions.indexOf(normalizedDealer);
  const safeDealerIndex = dealerIndex >= 0 ? dealerIndex : 0;
  // bidNumber is 1-indexed, so subtract 1 for array index
  const positionIndex = (safeDealerIndex + (bidNumber - 1)) % 4;
  return positions[positionIndex];
};

// Main component
const BidReviewPage = ({
  handId,
  onBack,
  onPrevHand,
  onNextHand,
  currentIndex,
  totalHands,
  // Review mode toggle (from ReviewPage wrapper)
  reviewMode,
  onSetReviewMode,
  biddingAvailable,
  playAvailable
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
  // CRITICAL FIX: Always recognize South's bids even if dealer data is missing
  const userBidNumbers = useMemo(() => {
    if (!handData?.auction_history) return [];

    const positions = ['N', 'E', 'S', 'W'];
    // Default to North as dealer if not specified (common convention)
    const normalizedDealer = normalizePosition(handData?.dealer || 'N');
    const dealerIndex = positions.indexOf(normalizedDealer);
    // Fallback to 0 if dealer position is invalid
    const safeDealerIndex = dealerIndex >= 0 ? dealerIndex : 0;
    const userBids = [];

    handData.auction_history.forEach((_, idx) => {
      const positionIndex = (safeDealerIndex + idx) % 4;
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
  // CRITICAL FIX: Use both the calculated list AND direct position check
  // to ensure South's moves are NEVER marked as AI plays
  const currentBidPosition = bidPosition > 0
    ? getPositionForBidNumber(bidPosition, handData?.dealer)
    : null;
  const isUserBidPosition = userBidNumbers.includes(bidPosition) ||
    currentBidPosition === userPosition;

  return (
    <div className="hand-review-page" data-testid="bid-review-page">
      {/* DD Table modal overlay */}
      {handData?.dd_analysis?.dd_table && chartExpanded && (
        <DDTableDisplay
          ddAnalysis={handData.dd_analysis}
          onDismiss={() => setChartExpanded(false)}
          asOverlay={true}
          showExplanation={true}
        />
      )}

      {/* Stage Container - Centered flexbox column for all content */}
      <div className="stage-container">
        {/* Header Bar - Constrained to table width */}
        <div className="header-bar">
          <button className="back-btn" onClick={onBack}>
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>

          <div className="header-mode-tabs">
            <button
              className={`mode-tab ${reviewMode === 'bidding' ? 'active' : ''}`}
              onClick={() => onSetReviewMode('bidding')}
              disabled={!biddingAvailable}
              title={!biddingAvailable ? 'No bidding data for this hand' : undefined}
            >
              Bidding
            </button>
            <button
              className={`mode-tab ${reviewMode === 'play' ? 'active' : ''}`}
              onClick={() => onSetReviewMode('play')}
              disabled={!playAvailable}
              title={!playAvailable ? 'No play data for this hand' : undefined}
            >
              Play
            </button>
          </div>

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

        {/* Pit Container - Fixed-Stack Footer Layout (matches HandReviewPage) */}
        <div className="pit-container">
          {/* LAYER 1: Replay Controls */}
          <div className="controls-layer">
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
          </div>

          {/* LAYER 2: Feedback Slot (Anti-Bounce Zone) */}
          <div className="feedback-slot">
            {totalBids > 0 && (() => {
              const isAiBid = !isUserBidPosition && bidPosition > 0 && !currentDecision;
              let aiBidLabel = null;
              if (isAiBid) {
                const posNames = { N: 'North', E: 'East', S: 'South', W: 'West' };
                const posName = posNames[currentBidPosition] || currentBidPosition;
                const bidText = handData?.auction_history?.[bidPosition - 1] || '';
                aiBidLabel = `${posName} bid ${bidText} — analysis is shown for your bids`;
              }
              return (
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
                  tricksCost={0}
                  isStart={bidPosition === 0}
                  isAiPlay={isAiBid}
                  aiPlayLabel={aiBidLabel}
                />
              );
            })()}
          </div>

        </div>
      </div>
    </div>
  );
};

export default BidReviewPage;
