/**
 * BiddingReplay Component (Flow 6)
 *
 * Spaced repetition review for bidding decisions.
 * Presents hands where the user previously made incorrect bids.
 *
 * Flow States: QUEUE_REVIEW -> PRESENT -> REBID -> EVALUATE -> SESSION_COMPLETE
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

// Shared components
import {
  FlowLayout,
  HandDisplay,
  BidTable,
  ResultStrip,
  InlineBid,
  PrimaryButton,
  SecondaryButton
} from '../../shared';

// Local dependencies
import { BiddingBox } from '../../../bridge/BiddingBox';
import {
  getDueItems,
  getQueueStats,
  INTERVALS
} from './spacedRepetition';
import {
  evaluateRebid,
  buildInfoStripMessage,
  calculateSessionStats,
  getHint
} from './BiddingReplay.logic';
import { CATEGORY_INFO, initializeMockData } from './mockData';

import './BiddingReplay.css';

// Flow states
const STATES = {
  QUEUE_REVIEW: 'QUEUE_REVIEW',
  PRESENT: 'PRESENT',
  REBID: 'REBID',
  EVALUATE: 'EVALUATE',
  SESSION_COMPLETE: 'SESSION_COMPLETE'
};

// Session size
const SESSION_SIZE = 5;

/**
 * BiddingReplay - Main component for spaced repetition bidding review
 *
 * @param {Object} props
 * @param {function} props.onClose - Called when flow is closed
 * @param {function} props.onComplete - Called with FlowResult when session ends
 */
function BiddingReplay({ onClose = null, onComplete = null }) {
  // State
  const [flowState, setFlowState] = useState(STATES.QUEUE_REVIEW);
  const [queueStats, setQueueStats] = useState(null);
  const [sessionItems, setSessionItems] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [results, setResults] = useState([]);
  const [currentResult, setCurrentResult] = useState(null);
  const [showHint, setShowHint] = useState(false);
  const [startTime] = useState(Date.now());

  // Load queue stats on mount
  useEffect(() => {
    // Initialize mock data if empty (for demo purposes)
    initializeMockData();

    // Load stats
    const stats = getQueueStats();
    setQueueStats(stats);
  }, []);

  // Current item being reviewed
  const currentItem = sessionItems[currentIndex] || null;

  /**
   * Start the review session
   */
  const handleStartSession = useCallback(() => {
    const items = getDueItems(SESSION_SIZE);
    if (items.length === 0) return;

    setSessionItems(items);
    setCurrentIndex(0);
    setResults([]);
    setFlowState(STATES.PRESENT);
  }, []);

  /**
   * Move from PRESENT to REBID state
   */
  const handleReadyToRebid = useCallback(() => {
    setShowHint(false);
    setFlowState(STATES.REBID);
  }, []);

  /**
   * Handle bid submission
   */
  const handleBid = useCallback((bid) => {
    if (!currentItem) return;

    const result = evaluateRebid({
      userBid: bid,
      correctBid: currentItem.correctBid,
      reviewItem: currentItem
    });

    setCurrentResult(result);
    setResults(prev => [...prev, result]);
    setFlowState(STATES.EVALUATE);
  }, [currentItem]);

  /**
   * Move to next item or complete session
   */
  const handleNext = useCallback(() => {
    if (currentIndex < sessionItems.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setCurrentResult(null);
      setShowHint(false);
      setFlowState(STATES.PRESENT);
    } else {
      setFlowState(STATES.SESSION_COMPLETE);
    }
  }, [currentIndex, sessionItems.length]);

  /**
   * Complete the session and emit result
   */
  const handleFinish = useCallback(() => {
    const stats = calculateSessionStats(results);

    const flowResult = {
      flowType: 'replay',
      handId: sessionItems.map(item => item.handId).join(','),
      timestamp: new Date().toISOString(),
      decisions: results.map((result, idx) => ({
        decisionId: sessionItems[idx]?.decisionPoint || `decision_${idx}`,
        category: sessionItems[idx]?.category || 'other',
        playerAnswer: result.userBid,
        correctAnswer: result.correctBid,
        isCorrect: result.isCorrect,
        conventionTag: sessionItems[idx]?.conventionTag
      })),
      overallScore: stats.correct > 0 ? Math.round((stats.correct / stats.total) * 100) : 0,
      timeSpent: Date.now() - startTime,
      conventionTags: [...new Set(sessionItems.map(item => item.conventionTag).filter(Boolean))]
    };

    if (onComplete) {
      onComplete(flowResult);
    }
    if (onClose) {
      onClose();
    }
  }, [results, sessionItems, startTime, onComplete, onClose]);

  /**
   * Format date for display
   */
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (dateStr === today.toISOString().split('T')[0]) {
      return 'Today';
    }
    if (dateStr === tomorrow.toISOString().split('T')[0]) {
      return 'Tomorrow';
    }

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  /**
   * Get performance class for score
   */
  const getScoreClass = (percentage) => {
    if (percentage >= 75) return 'good';
    if (percentage >= 50) return 'medium';
    return 'weak';
  };

  // Render step indicator
  const getStepIndicator = () => {
    if (flowState === STATES.QUEUE_REVIEW) return null;
    if (flowState === STATES.SESSION_COMPLETE) return 'Complete';
    return `Hand ${currentIndex + 1} of ${sessionItems.length}`;
  };

  // Render progress dots
  const renderProgressDots = () => {
    return (
      <div className="replay-progress">
        {sessionItems.map((item, idx) => {
          let className = 'replay-progress-dot';
          if (idx < results.length) {
            className += results[idx]?.isCorrect ? ' completed' : ' incorrect';
          } else if (idx === currentIndex) {
            className += ' current';
          }
          return <div key={idx} className={className} />;
        })}
      </div>
    );
  };

  // Build info strip with InlineBid components
  const renderInfoStrip = () => {
    if (!currentItem) return null;
    const info = buildInfoStripMessage(currentItem);

    return (
      <div className="replay-info-strip">
        <span className="replay-info-icon">&#128257;</span>
        <span className="replay-info-text">
          {info.prefix} <InlineBid bid={info.previousBid} />.{' '}
          {info.middle} <InlineBid bid={info.correctBid} />.{' '}
          {info.suffix}
        </span>
      </div>
    );
  };

  // Render content based on state
  const renderFeltContent = () => {
    switch (flowState) {
      case STATES.QUEUE_REVIEW:
        return null; // No felt content for queue review

      case STATES.PRESENT:
      case STATES.REBID:
      case STATES.EVALUATE:
        if (!currentItem?.handData) return null;
        return (
          <div className="replay-hand-area">
            <div className="replay-hand-header">
              <span className="replay-hcp-badge">
                {currentItem.handData.hcp || '?'} HCP
              </span>
              <span className="replay-vulnerability-badge">
                Vul: {currentItem.handData.vulnerability || 'None'}
              </span>
            </div>
            <HandDisplay
              cards={currentItem.handData.hand}
              mode="hand-h"
            />
            {renderProgressDots()}
          </div>
        );

      case STATES.SESSION_COMPLETE:
        return null;

      default:
        return null;
    }
  };

  const renderInteractionContent = () => {
    switch (flowState) {
      case STATES.QUEUE_REVIEW:
        return renderQueueReview();

      case STATES.PRESENT:
        return renderPresent();

      case STATES.REBID:
        return renderRebid();

      case STATES.EVALUATE:
        return renderEvaluate();

      case STATES.SESSION_COMPLETE:
        return renderSessionComplete();

      default:
        return null;
    }
  };

  const renderQueueReview = () => {
    if (!queueStats) {
      return <div className="replay-queue-review">Loading...</div>;
    }

    if (queueStats.dueToday === 0) {
      return (
        <div className="replay-empty-state">
          <div className="replay-empty-icon">&#10003;</div>
          <h3 className="replay-empty-title">All caught up!</h3>
          <p className="replay-empty-message">
            No hands due for review today. Come back tomorrow or play more hands to build your review queue.
          </p>
          <PrimaryButton onClick={onClose}>
            Back to Learning
          </PrimaryButton>
        </div>
      );
    }

    return (
      <div className="replay-queue-review">
        <h2 className="replay-queue-title">Practice Your Weak Spots</h2>
        <p className="replay-queue-subtitle">
          Review hands where you made bidding mistakes
        </p>

        <div className="replay-queue-stats">
          <div className="replay-stat-item">
            <span className="replay-stat-value">{queueStats.dueToday}</span>
            <span className="replay-stat-label">Due Today</span>
          </div>
          <div className="replay-stat-item">
            <span className="replay-stat-value">{queueStats.total}</span>
            <span className="replay-stat-label">In Queue</span>
          </div>
          <div className="replay-stat-item">
            <span className="replay-stat-value">{queueStats.avgAccuracy}%</span>
            <span className="replay-stat-label">Accuracy</span>
          </div>
        </div>

        {Object.keys(queueStats.byCategory).length > 0 && (
          <div className="replay-categories">
            {Object.entries(queueStats.byCategory).map(([category, stats]) => (
              <div key={category} className="replay-category-item">
                <span className="replay-category-name">
                  {CATEGORY_INFO[category]?.name || category}
                </span>
                <span className="replay-category-count">
                  {stats.due} due
                </span>
              </div>
            ))}
          </div>
        )}

        <PrimaryButton onClick={handleStartSession}>
          Start Review ({Math.min(queueStats.dueToday, SESSION_SIZE)} hands)
        </PrimaryButton>
      </div>
    );
  };

  const renderPresent = () => {
    if (!currentItem?.handData) return null;

    return (
      <>
        {renderInfoStrip()}
        <div className="replay-bidding-area">
          <div className="replay-auction-section">
            <div className="replay-section-label">Auction So Far</div>
            <BidTable
              bids={currentItem.handData.auction}
              dealer={currentItem.handData.dealer || 'N'}
              playerSeat="S"
            />
          </div>

          <PrimaryButton onClick={handleReadyToRebid}>
            I'm Ready to Bid
          </PrimaryButton>
        </div>
      </>
    );
  };

  const renderRebid = () => {
    if (!currentItem?.handData) return null;

    return (
      <>
        {renderInfoStrip()}
        <div className="replay-bidding-area">
          <div className="replay-auction-section">
            <div className="replay-section-label">Auction So Far</div>
            <BidTable
              bids={currentItem.handData.auction}
              dealer={currentItem.handData.dealer || 'N'}
              playerSeat="S"
            />
          </div>

          <div className="replay-bidding-box-container">
            <BiddingBox
              onBid={handleBid}
              disabled={false}
              auction={currentItem.handData.auction}
            />
          </div>

          {!showHint ? (
            <button
              className="replay-hint-button"
              onClick={() => setShowHint(true)}
            >
              <span>?</span> Need a hint?
            </button>
          ) : (
            <div className="replay-hint-text">
              {getHint(currentItem)}
            </div>
          )}
        </div>
      </>
    );
  };

  const renderEvaluate = () => {
    if (!currentResult) return null;

    return (
      <div className="replay-result-area">
        <div className="replay-result-strip">
          <ResultStrip
            type={currentResult.isCorrect ? 'success' : 'error'}
            message={currentResult.isCorrect
              ? 'Correct!'
              : `You bid ${currentResult.userBid}. The correct bid is ${currentResult.correctBid}.`}
          />
        </div>

        {currentResult.nextReviewInfo && (
          <div className="replay-interval-update">
            <span className="replay-interval-icon">
              {currentResult.nextReviewInfo.status === 'mastered' ? '&#127942;' :
               currentResult.isCorrect ? '&#128640;' : '&#128257;'}
            </span>
            <span className="replay-interval-text">
              {currentResult.nextReviewInfo.message}
            </span>
          </div>
        )}

        <div className="replay-explanation">
          {currentResult.explanation}
        </div>

        <div className="replay-next-button">
          <PrimaryButton onClick={handleNext}>
            {currentIndex < sessionItems.length - 1 ? 'Next Hand' : 'See Results'}
          </PrimaryButton>
        </div>
      </div>
    );
  };

  const renderSessionComplete = () => {
    const stats = calculateSessionStats(results);

    return (
      <div className="replay-complete">
        <div className="replay-complete-header">
          <h2 className="replay-complete-title">Session Complete!</h2>
          <div className="replay-complete-score">
            {stats.correct}/{stats.total}
          </div>
          <div className="replay-complete-label">correct</div>
        </div>

        {stats.masteredCount > 0 && (
          <div className="replay-mastered-count">
            <span>&#127942;</span>
            {stats.masteredCount} hand{stats.masteredCount !== 1 ? 's' : ''} mastered!
          </div>
        )}

        {stats.categoryBreakdown.length > 0 && (
          <div className="replay-category-results">
            <h4>By Category</h4>
            {stats.categoryBreakdown.map(cat => (
              <div key={cat.category} className="replay-category-result">
                <div className="replay-category-info">
                  <span className={`replay-category-trend ${cat.trend}`}></span>
                  <span>{CATEGORY_INFO[cat.category]?.name || cat.category}</span>
                </div>
                <span className={`replay-category-score ${getScoreClass(cat.percentage)}`}>
                  {cat.correct}/{cat.total}
                </span>
              </div>
            ))}
          </div>
        )}

        {stats.nextReviews.length > 0 && (
          <div className="replay-next-reviews">
            <h4>Next Reviews</h4>
            {stats.nextReviews.slice(0, 5).map((review, idx) => (
              <div key={idx} className="replay-review-item">
                <span className="replay-review-category">
                  {CATEGORY_INFO[review.category]?.name || review.category}
                </span>
                <span className="replay-review-date">
                  {formatDate(review.nextDate)}
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="replay-actions">
          <PrimaryButton onClick={handleFinish}>
            Done
          </PrimaryButton>
          <SecondaryButton onClick={() => {
            const newItems = getDueItems(SESSION_SIZE);
            if (newItems.length > 0) {
              setSessionItems(newItems);
              setCurrentIndex(0);
              setResults([]);
              setCurrentResult(null);
              setFlowState(STATES.PRESENT);
            } else {
              handleFinish();
            }
          }}>
            Review More
          </SecondaryButton>
        </div>
      </div>
    );
  };

  return (
    <FlowLayout
      title="Bidding Review"
      stepIndicator={getStepIndicator()}
      onClose={onClose}
      feltContent={renderFeltContent()}
      interactionContent={renderInteractionContent()}
    />
  );
}

BiddingReplay.propTypes = {
  onClose: PropTypes.func,
  onComplete: PropTypes.func
};

export default BiddingReplay;
