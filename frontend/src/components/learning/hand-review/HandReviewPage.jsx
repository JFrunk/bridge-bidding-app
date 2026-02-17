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

import React, { useState, useEffect, useCallback } from 'react';
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
  normalizeSuit,
  isRedSuit,
} from './constants';
import DecayChart from '../../analysis/DecayChart';
import HeuristicScorecard from '../HeuristicScorecard';
import ReactorLayout from '../../layout/ReactorLayout';
import TrickArena from '../../shared/TrickArena';
import { ReplayHorizontalHand, ReplaySuitStack } from './ReplayHand';
import FeedbackDashboard from './FeedbackDashboard';
import './HandReviewPage.css';

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
  if (!decision) return 'no-data';

  // No stored analysis — don't claim it was good
  if (decision.is_basic_info) return 'no-data';

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
      return 'no-data';
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

  // Priority: feedback > reasoning > signal_reason > helpful_hint
  if (decision.feedback) return decision.feedback;
  if (decision.reasoning) return decision.reasoning;
  if (decision.signal_reason) return decision.signal_reason;
  if (decision.helpful_hint) return decision.helpful_hint;

  // No stored analysis — don't fabricate a positive assessment
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
  onViewProgress,
  // Review mode toggle (from ReviewPage wrapper)
  reviewMode,
  onSetReviewMode,
  biddingAvailable,
  playAvailable
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
      {/* DecayChart modal overlay */}
      {handData?.decay_curve && chartExpanded && (
        <div className="analysis-modal-overlay" onClick={() => setChartExpanded(false)}>
          <div className="analysis-modal-content" onClick={e => e.stopPropagation()}>
            <div className="analysis-modal-header">
              <h3 className="analysis-modal-title">Trick Potential Analysis</h3>
              <button
                className="analysis-modal-close"
                onClick={() => setChartExpanded(false)}
                aria-label="Close"
              >
                &times;
              </button>
            </div>
            <div className="analysis-modal-body">
              <DecayChart
                data={handData.decay_curve}
                replayPosition={replayPosition}
                onPositionChange={setReplayPosition}
              />
            </div>
          </div>
        </div>
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
            {(() => {
              const isAi = !currentReplayDecision && replayPosition > 0;
              let aiLabel = null;
              if (isAi && handData?.play_history) {
                const play = handData.play_history[replayPosition - 1];
                if (play) {
                  const posNames = { N: 'North', E: 'East', S: 'South', W: 'West' };
                  const pos = play.player || play.position;
                  const posName = posNames[pos] || pos;
                  const rank = play.rank || play.r;
                  const suit = normalizeSuit(play.suit || play.s);
                  aiLabel = `${posName} played ${rank}${suit} — analysis is shown for your cards`;
                }
              }
              return (
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
                  isAiPlay={isAi}
                  aiPlayLabel={aiLabel}
                  isVisible={tricks.length > 0}
                />
              );
            })()}
          </div>

          {/* LAYER 3: Heuristic Scorecard (inline when decision has data) */}
          {currentReplayDecision && !currentReplayDecision.is_basic_info && (
            <div className="expandable-layer">
              <div className="heuristic-panel">
                <HeuristicScorecard decision={currentReplayDecision} />
              </div>
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
