/**
 * HandReviewPage - Consolidated Play-by-Play Review Page
 *
 * Single full-screen page for reviewing hand play.
 * Replaces both HandReviewModal and the old HandReviewPage.
 *
 * Design principles:
 * - Everything fits on one screen (no scrolling for core content)
 * - Single compact header with all controls
 * - Horizontal card layout for E/W (not vertical)
 * - Collapsible decay chart
 * - Inline feedback (not modal)
 *
 * Entry points:
 * - After hand completion (returns to play screen)
 * - From My Progress (returns to progress)
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useHandReview } from './useHandReview';
import {
  RATING_CONFIG,
  POSITION_LABELS,
  RANK_DISPLAY,
  getSuitOrder,
  normalizeSuit,
  isRedSuit,
  groupCardsBySuit
} from './constants';
import DecayChart from '../../analysis/DecayChart';
import HeuristicScorecard from '../HeuristicScorecard';
import './HandReviewPage.css';

// Compact card component for replay display
const ReplayCard = ({ card, compact = false }) => {
  const rank = card.rank || card.r;
  const suit = normalizeSuit(card.suit || card.s);
  const displayRank = RANK_DISPLAY[rank] || rank;
  const redSuit = isRedSuit(suit);

  return (
    <div className={`replay-card ${compact ? 'compact' : ''} ${redSuit ? 'red' : 'black'}`}>
      <span className="rank">{displayRank}</span>
      <span className="suit">{suit}</span>
    </div>
  );
};

// Hand display component - horizontal layout for all positions
const ReplayHandDisplay = ({ cards, position, trumpStrain, compact = false }) => {
  const suitOrder = getSuitOrder(trumpStrain);
  const cardsBySuit = useMemo(() => groupCardsBySuit(cards), [cards]);

  return (
    <div className={`replay-hand ${compact ? 'compact' : ''}`}>
      <div className="hand-cards">
        {suitOrder.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (suitCards.length === 0) return null;
          return (
            <div key={suit} className="suit-group">
              {suitCards.map((card) => (
                <ReplayCard
                  key={`${card.rank}-${card.suit}`}
                  card={card}
                  compact={compact}
                />
              ))}
            </div>
          );
        })}
        {cards.length === 0 && (
          <div className="hand-empty">-</div>
        )}
      </div>
    </div>
  );
};

// Trick display component - compact compass layout
const ReplayTrickDisplay = ({ trick, leader, trickNumber }) => {
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

  return (
    <div className="trick-display">
      <div className="trick-info">
        <span className="trick-number">Trick {trickNumber}</span>
        {leader && <span className="trick-leader">Lead: {leader}</span>}
      </div>
      <div className="trick-card-north">
        {cardByPosition.N && <ReplayCard card={cardByPosition.N} />}
      </div>
      <div className="trick-card-west">
        {cardByPosition.W && <ReplayCard card={cardByPosition.W} />}
      </div>
      <div className="trick-card-east">
        {cardByPosition.E && <ReplayCard card={cardByPosition.E} />}
      </div>
      <div className="trick-card-south">
        {cardByPosition.S && <ReplayCard card={cardByPosition.S} />}
      </div>
    </div>
  );
};

// Center info box - shown at position 0 (start)
const CenterInfoBox = ({ contract, vulnerability, dealer }) => {
  // Parse contract for color
  const suitMatch = contract?.match(/[SHDC\u2660\u2665\u2666\u2663]/i);
  const isRed = suitMatch && isRedSuit(suitMatch[0]);

  return (
    <div className="center-info-box">
      <div className={`center-contract ${isRed ? 'red' : ''}`}>{contract}</div>
      <div className="center-meta">
        <span>Vul: {vulnerability || 'None'}</span>
        <span>Dealer: {dealer}</span>
      </div>
    </div>
  );
};

// Feedback bar component - compact single-line feedback
const FeedbackBar = ({ decision, isStart }) => {
  // Start state hint
  if (isStart) {
    return (
      <div className="feedback-bar hint">
        <span className="hint-icon">{'\u261D'}</span>
        <span className="hint-text">
          Press <span className="key-hint">{'\u25B6'} Next</span> or use <kbd>{'\u2190'}</kbd> <kbd>{'\u2192'}</kbd> arrow keys to step through each play
        </span>
      </div>
    );
  }

  // No decision (AI play)
  if (!decision) {
    return (
      <div className="feedback-bar ai-play">
        <span className="feedback-text muted">AI play \u2014 no feedback recorded</span>
      </div>
    );
  }

  // Basic info (no DDS analysis)
  if (decision.is_basic_info) {
    const posName = POSITION_LABELS[decision.position];
    return (
      <div className="feedback-bar basic">
        <span className="played-info">
          <strong>{posName}</strong> played <span className={`card-text ${isRedSuit(decision.user_card?.slice(-1)) ? 'red' : 'black'}`}>{decision.user_card}</span>
        </span>
        <span className="feedback-text muted">No detailed analysis recorded</span>
      </div>
    );
  }

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

  const effectiveRating = (isSignalFeedback && !suppressSignalFeedback) ? 'suboptimal_signal' : decision.rating;
  const config = RATING_CONFIG[effectiveRating] || RATING_CONFIG.good;
  const posName = POSITION_LABELS[decision.position];
  const cardSuit = decision.user_card?.slice(-1);

  return (
    <div className="feedback-bar" style={{ borderLeftColor: config.color, backgroundColor: config.bgColor }}>
      <span className="feedback-badge" style={{ backgroundColor: config.color }}>
        {config.icon} {config.label}
      </span>

      <span className="played-info">
        <strong>{posName}</strong> played <span className={`card-text ${isRedSuit(cardSuit) ? 'red' : 'black'}`}>{decision.user_card}</span>
      </span>

      {decision.optimal_card && decision.optimal_card !== decision.user_card && decision.rating !== 'optimal' && (
        <span className="better-play">
          Better: <span className={`card-text ${isRedSuit(decision.optimal_card?.slice(-1)) ? 'red' : 'black'}`}>{decision.optimal_card}</span>
        </span>
      )}

      {decision.tricks_cost > 0 && (
        <span className="tricks-cost">-{decision.tricks_cost} trick{decision.tricks_cost !== 1 ? 's' : ''}</span>
      )}

      {decision.feedback && (
        <span className="feedback-text">{decision.feedback}</span>
      )}
    </div>
  );
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
      {/* Header Bar - Single compact bar with all controls */}
      <div className="header-bar">
        <button className="back-btn" onClick={onBack}>\u2190 Back</button>

        <div className="contract-summary">
          <span className={`contract-badge ${isRedSuit(handData?.contract?.match(/[SHDC\u2660\u2665\u2666\u2663]/i)?.[0]) ? 'red' : ''}`}>
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

        {/* Navigation controls */}
        <div className="nav-controls">
          <button className="nav-btn" onClick={goToStart} disabled={replayPosition <= 0} title="Start (Home)">\u23ee</button>
          <button className="nav-btn" onClick={goPrev} disabled={replayPosition <= 0}>\u25c0</button>
          <span className="nav-counter">
            {replayPosition === 0 ? 'Start' : `${replayPosition}/${totalPlays}`}
          </span>
          <button className="nav-btn" onClick={goNext} disabled={replayPosition >= totalPlays} data-testid="nav-next">\u25b6</button>
          <button className="nav-btn" onClick={goToEnd} disabled={replayPosition >= totalPlays} title="End (End)">\u23ed</button>

          {/* Hand navigation (when multiple hands) */}
          {totalHands > 1 && (
            <div className="hand-nav">
              <button className="nav-btn small" onClick={onPrevHand} disabled={!onPrevHand}>\u25c0</button>
              <span className="hand-counter">{currentIndex + 1}/{totalHands}</span>
              <button className="nav-btn small" onClick={onNextHand} disabled={!onNextHand}>\u25b6</button>
            </div>
          )}
        </div>

        <button
          className={`chart-toggle ${chartExpanded ? 'active' : ''}`}
          onClick={() => setChartExpanded(!chartExpanded)}
          title="Toggle decay chart"
        >
          \ud83d\udcca
        </button>
      </div>

      {/* Compass Table - Main play area */}
      <div className="compass-table">
        {/* North */}
        <div className="position-area north-area">
          <div className="pos-label">North</div>
          {remainingHands && (
            <ReplayHandDisplay cards={remainingHands.N} position="N" trumpStrain={trumpStrain} />
          )}
        </div>

        {/* West */}
        <div className="position-area west-area">
          <div className="pos-label">West</div>
          {remainingHands && (
            <ReplayHandDisplay cards={remainingHands.W} position="W" trumpStrain={trumpStrain} compact />
          )}
        </div>

        {/* Center - Trick or Info */}
        <div className="center-area">
          {replayPosition === 0 ? (
            <CenterInfoBox
              contract={handData?.contract}
              vulnerability={handData?.vulnerability}
              dealer={handData?.dealer}
            />
          ) : (
            <ReplayTrickDisplay
              trick={currentReplayTrick}
              leader={currentReplayLeader}
              trickNumber={currentReplayTrickNumber}
            />
          )}
        </div>

        {/* East */}
        <div className="position-area east-area">
          <div className="pos-label">East</div>
          {remainingHands && (
            <ReplayHandDisplay cards={remainingHands.E} position="E" trumpStrain={trumpStrain} compact />
          )}
        </div>

        {/* South */}
        <div className="position-area south-area">
          {remainingHands && (
            <ReplayHandDisplay cards={remainingHands.S} position="S" trumpStrain={trumpStrain} />
          )}
          <div className="pos-label">South (You)</div>
        </div>
      </div>

      {/* Feedback Bar */}
      {tricks.length > 0 && (
        <FeedbackBar
          decision={currentReplayDecision}
          isStart={replayPosition === 0}
        />
      )}

      {/* Decay Chart (Collapsible) */}
      {handData?.decay_curve && (
        <div className={`chart-panel ${chartExpanded ? 'expanded' : 'collapsed'}`}>
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

      {/* Action buttons (post-hand flow) */}
      {(onPlayAnother || onReplay || onViewProgress) && (
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
      )}
    </div>
  );
};

export default HandReviewPage;
