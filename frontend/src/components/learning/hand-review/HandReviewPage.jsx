/**
 * HandReviewPage - Consolidated Play-by-Play Review Page
 *
 * System v2.0 compliant - Uses ReactorLayout for consistent table layout.
 * Matches the Gameplay Page for consistent user mental model.
 *
 * Entry points:
 * - After hand completion (returns to play screen)
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
import { useHandReview } from './useHandReview';
import {
  POSITION_LABELS,
  getSuitOrder,
  normalizeSuit,
  isRedSuit,
  groupCardsBySuit,
  sortCards
} from './constants';
import DecayChart from '../../analysis/DecayChart';
import HeuristicScorecard from '../HeuristicScorecard';
import ReactorLayout from '../../layout/ReactorLayout';
import TrickArena from '../../shared/TrickArena';
import Card from '../../../shared/components/Card';
import FeedbackDashboard from './FeedbackDashboard';
import './HandReviewPage.css';

/**
 * ReplayHorizontalHand - Physics v2.0 compliant horizontal hand for N/S positions
 */
const ReplayHorizontalHand = ({ cards, position, trumpStrain, scaleClass = 'text-base', isUser = false }) => {
  const suitOrder = getSuitOrder(trumpStrain);
  const cardsBySuit = useMemo(() => {
    const grouped = groupCardsBySuit(cards);
    // Sort each suit
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
const ReplaySuitStack = ({ cards, position, trumpStrain, scaleClass = 'text-sm' }) => {
  const suitOrder = getSuitOrder(trumpStrain);
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

// Helper to convert trick to TrickArena format
const formatTrickForArena = (trick) => {
  const cards = {};
  if (!trick) return cards;
  trick.forEach(play => {
    const pos = play.player || play.position;
    cards[pos] = {
      rank: play.rank || play.r,
      suit: normalizeSuit(play.suit || play.s)
    };
  });
  return cards;
};

/**
 * Map decision rating to FeedbackDashboard grade
 */
const mapRatingToGrade = (decision) => {
  if (!decision) return 'reasonable';

  // Check for signal feedback (no trick cost but signal issue)
  const isSignalFeedback = decision.signal_reason && decision.tricks_cost === 0 && !decision.is_signal_optimal;
  const reasoning = (decision.reasoning || '').toLowerCase();
  const correctIndicators = ['correct', 'conserving', 'optimal', 'good', 'right', 'best', 'perfect'];
  const reasoningSaysCorrect = correctIndicators.some(ind => reasoning.includes(ind));

  let suppressSignalFeedback = false;
  if (isSignalFeedback && decision.rating === 'optimal' && reasoningSaysCorrect) {
    suppressSignalFeedback = true;
  }
  if (isSignalFeedback && decision.is_signal_optimal) {
    suppressSignalFeedback = true;
  }

  const effectiveRating = (isSignalFeedback && !suppressSignalFeedback) ? 'suboptimal' : decision.rating;

  // Map rating to grade
  switch (effectiveRating) {
    case 'optimal':
      return 'optimal';
    case 'good':
      return 'reasonable';
    case 'suboptimal':
    case 'suboptimal_signal':
      return 'questionable';
    case 'blunder':
      return 'blunder';
    default:
      return 'reasonable';
  }
};

/**
 * Parse a card string like "A♠" or "10H" into {rank, suit}
 */
const parseCardString = (cardStr) => {
  if (!cardStr || typeof cardStr !== 'string') return null;

  // Handle suit symbols
  const suitMap = { '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' };
  let suit = cardStr.slice(-1);
  let rank = cardStr.slice(0, -1);

  // Check for symbol suits
  if (suitMap[suit]) {
    suit = suitMap[suit];
  }

  return { rank, suit };
};

/**
 * Build analysis text from decision data
 */
const buildAnalysisText = (decision) => {
  if (!decision) return null;

  // Priority: feedback > reasoning > signal_reason
  if (decision.feedback) return decision.feedback;
  if (decision.reasoning) return decision.reasoning;
  if (decision.signal_reason) return decision.signal_reason;

  // Fallback based on rating
  const grade = mapRatingToGrade(decision);
  if (grade === 'optimal') return 'This was the best play in this position.';
  if (grade === 'reasonable') return 'A solid choice that maintains your position.';

  return null;
};

// Main component
const HandReviewPage = ({
  handId,
  onBack,
  // Hand navigation (when reviewing multiple hands)
  onPrevHand,
  onNextHand,
  currentIndex,
  totalHands,
  // Action buttons (for post-hand flow)
  onPlayAnother,
  onReplay,
  onViewProgress
}) => {
  const [chartExpanded, setChartExpanded] = useState(false);

  const {
    handData,
    loading,
    error,
    replayPosition,
    setReplayPosition,
    totalPlays,
    tricks,
    trumpStrain,
    remainingHands,
    currentReplayTrick,
    currentReplayTrickNumber,
    currentReplayLeader,
    currentReplayDecision,
    userRole,
    getScoreForUser,
    getResultForUser,
    goToStart,
    goToEnd,
    goNext,
    goPrev
  } = useHandReview(handId);

  // Keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape' && onBack) {
      onBack();
      return;
    }
    if (e.key === 'ArrowLeft') goPrev();
    else if (e.key === 'ArrowRight') goNext();
    else if (e.key === 'Home') goToStart();
    else if (e.key === 'End') goToEnd();
  }, [onBack, goPrev, goNext, goToStart, goToEnd]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Loading state
  if (loading) {
    return (
      <div className="hand-review-page">
        <div className="loading-state">Loading hand...</div>
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

  const result = getResultForUser();
  const userScore = getScoreForUser();

  return (
    <div className="hand-review-page" data-testid="hand-review-page">
      {/* Stage Container - Centered flexbox column for all content */}
      <div className="stage-container">
        {/* Header Bar - Constrained to table width */}
        <div className="header-bar">
          <button className="back-btn" onClick={onBack}>
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>

          <div className="contract-summary">
            <span className={`contract-badge ${isRedSuit(handData?.contract?.match(/[SHDC♠♥♦♣]/i)?.[0]) ? 'red' : ''}`}>
              {handData?.contract || 'Unknown'}
            </span>
            <span className="contract-by">by {POSITION_LABELS[handData?.contract_declarer] || handData?.contract_declarer}</span>
            <span className={`result-badge ${result.isGood ? 'success' : 'failure'}`}>
              {result.text}
              {result.detail && <span className="result-detail"> {result.detail}</span>}
            </span>
            <span className="role-badge">{userRole}</span>
            <span className={`score-badge ${userScore >= 0 ? 'positive' : 'negative'}`}>
              {userScore > 0 ? '+' : ''}{userScore}
            </span>
            {handData?.play_quality_summary?.has_data && (
              <span className="accuracy-badge">{handData.play_quality_summary.accuracy_rate}% play</span>
            )}
          </div>

          <button
            className={`chart-toggle ${chartExpanded ? 'active' : ''}`}
            onClick={() => setChartExpanded(!chartExpanded)}
            title="Toggle decay chart"
          >
            <BarChart2 size={18} />
          </button>
        </div>

        {/* ReactorLayout - System v2.0 compliant table layout */}
        {remainingHands && (
          <ReactorLayout
            className="replay-reactor"
            scaleClass="text-base"
            north={
              <ReplayHorizontalHand
                cards={remainingHands.N}
                position="N"
                trumpStrain={trumpStrain}
                scaleClass="text-lg"
              />
            }
            south={
              <ReplayHorizontalHand
                cards={remainingHands.S}
                position="S"
                trumpStrain={trumpStrain}
                scaleClass="text-xl"
                isUser={true}
              />
            }
            east={
              <ReplaySuitStack
                cards={remainingHands.E}
                position="E"
                trumpStrain={trumpStrain}
                scaleClass="text-sm"
              />
            }
            west={
              <ReplaySuitStack
                cards={remainingHands.W}
                position="W"
                trumpStrain={trumpStrain}
                scaleClass="text-sm"
              />
            }
            center={
              <TrickArena
                playedCards={formatTrickForArena(currentReplayTrick)}
                scaleClass="text-base"
              />
            }
          />
        )}

        {/* Pit Container - Fixed-Stack Footer Layout */}
        <div className="pit-container">
          {/* LAYER 1: Replay Controls (Gray Bar) - Fixed at top */}
          <div className="controls-layer">
            <div className="replay-controls">
              <button className="replay-btn icon-only" onClick={goToStart} disabled={replayPosition <= 0} title="Start (Home)">
                <SkipBack size={18} />
              </button>
              <button className="replay-btn prev" onClick={goPrev} disabled={replayPosition <= 0}>
                <ChevronLeft size={18} />
                <span>Prev</span>
              </button>
              <span className="replay-counter">
                {replayPosition === 0 ? 'Start' : `Play ${replayPosition} of ${totalPlays}`}
              </span>
              <button className="replay-btn next primary" onClick={goNext} disabled={replayPosition >= totalPlays} data-testid="nav-next">
                <span>Next</span>
                <ChevronRight size={18} />
              </button>
              <button className="replay-btn icon-only" onClick={goToEnd} disabled={replayPosition >= totalPlays} title="End (End)">
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

          {/* LAYER 2: Feedback Slot (Anti-Bounce Zone) - Fixed height */}
          <div className="feedback-slot">
            <FeedbackDashboard
              grade={currentReplayDecision ? mapRatingToGrade(currentReplayDecision) : 'reasonable'}
              analysisText={buildAnalysisText(currentReplayDecision)}
              alternativePlay={
                currentReplayDecision?.optimal_card &&
                currentReplayDecision.optimal_card !== currentReplayDecision.user_card
                  ? parseCardString(currentReplayDecision.optimal_card)
                  : null
              }
              playedCard={currentReplayDecision?.user_card ? parseCardString(currentReplayDecision.user_card) : null}
              tricksCost={currentReplayDecision?.tricks_cost || 0}
              isStart={replayPosition === 0}
              isAiPlay={!currentReplayDecision && replayPosition > 0}
              isVisible={tricks.length > 0}
            />
          </div>

          {/* LAYER 3: Expandable Content (Charts, Heuristics) */}
          {(chartExpanded || (currentReplayDecision && !currentReplayDecision.is_basic_info)) && (
            <div className="expandable-layer">
              {/* Decay Chart (Collapsible) */}
              {handData?.decay_curve && chartExpanded && (
                <div className="chart-panel expanded">
                  <DecayChart
                    data={handData.decay_curve}
                    replayPosition={replayPosition}
                    onPositionChange={setReplayPosition}
                  />
                </div>
              )}

              {/* Heuristic Scorecard (if decision has data) */}
              {currentReplayDecision && !currentReplayDecision.is_basic_info && (
                <div className="heuristic-panel">
                  <HeuristicScorecard decision={currentReplayDecision} />
                </div>
              )}
            </div>
          )}

          {/* LAYER 4: Action Buttons (Beige Bar) - Fixed at bottom */}
          {(onPlayAnother || onReplay || onViewProgress) && (
            <div className="action-layer">
              <div className="action-bar">
                {onPlayAnother && (
                  <button className="action-btn primary" onClick={onPlayAnother}>Play Another</button>
                )}
                {onReplay && (
                  <button className="action-btn secondary" onClick={onReplay}>Replay Hand</button>
                )}
                {onViewProgress && (
                  <button className="action-btn secondary" onClick={onViewProgress}>My Progress</button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HandReviewPage;
