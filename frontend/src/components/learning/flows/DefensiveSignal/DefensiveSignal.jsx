/**
 * DefensiveSignal.jsx
 * Flow 7: Defensive Signal Quiz
 *
 * Teaches players to give correct defensive signals:
 * - Attitude (encourage/discourage)
 * - Count (even/odd)
 * - Suit Preference (higher/lower suit)
 *
 * Flow States: LEVEL_SELECT -> PRESENT -> SELECT_CARD -> RESULT -> SESSION_SUMMARY
 */

import React, { useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  FlowLayout,
  HandDisplay,
  ResultStrip,
  PrimaryButton,
  SecondaryButton,
} from '../../shared';
import { SUIT_SYMBOLS, SUIT_ORDER, sortCards, groupBySuit } from '../../types/hand-types';
import {
  getSituationsByLevel,
  getShuffledSituations,
} from './mockData';
import {
  SIGNAL_TYPE_INFO,
  evaluateSignal,
  calculateSummary,
  buildFlowResult,
} from './DefensiveSignal.logic';
import './DefensiveSignal.css';

/**
 * Flow states
 */
const STATES = {
  LEVEL_SELECT: 'LEVEL_SELECT',
  PRESENT: 'PRESENT',
  SELECT_CARD: 'SELECT_CARD',
  RESULT: 'RESULT',
  SESSION_SUMMARY: 'SESSION_SUMMARY',
};

/**
 * Level options for level select
 */
const LEVEL_OPTIONS = [
  { level: 1, name: 'Attitude', desc: 'High = encourage, Low = discourage' },
  { level: 2, name: 'Count', desc: 'High-low = even, Low-high = odd' },
  { level: 3, name: 'Suit Preference', desc: 'High = higher suit, Low = lower' },
  { level: 0, name: 'Mixed Practice', desc: 'All signal types combined' },
];

/**
 * Get performance level class
 */
const getPerformanceClass = (accuracy) => {
  if (accuracy === null) return 'na';
  if (accuracy >= 75) return 'good';
  if (accuracy >= 50) return 'medium';
  return 'weak';
};

/**
 * Check if suit is red
 */
const isRedSuit = (suit) => suit === 'H' || suit === 'D';

/**
 * DummyDiagram - Compact hand diagram for dummy display
 */
const DummyDiagram = ({ cards }) => {
  const grouped = groupBySuit(cards);

  return (
    <div className="signal-dummy-diagram">
      {SUIT_ORDER.map((suit) => {
        const suitCards = grouped[suit] || [];
        const ranksDisplay =
          suitCards.length > 0
            ? suitCards.map((c) => c.rank).join(' ')
            : '\u2014';

        return (
          <div key={suit} className="suit-line">
            <span className={`suit-sym ${suit.toLowerCase()}`}>
              {SUIT_SYMBOLS[suit]}
            </span>
            <span className="ranks">{ranksDisplay}</span>
          </div>
        );
      })}
    </div>
  );
};

DummyDiagram.propTypes = {
  cards: PropTypes.arrayOf(
    PropTypes.shape({
      rank: PropTypes.string.isRequired,
      suit: PropTypes.oneOf(['S', 'H', 'D', 'C']).isRequired,
    })
  ).isRequired,
};

/**
 * CardDisplay - Single card for result display
 */
const CardDisplay = ({ rank, suit, variant }) => {
  const isRed = isRedSuit(suit);
  const classes = [
    'signal-card-display',
    isRed ? 'red' : 'black',
    variant || '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes}>
      <span className="signal-card-rank">{rank}</span>
      <span className="signal-card-suit">{SUIT_SYMBOLS[suit]}</span>
    </div>
  );
};

CardDisplay.propTypes = {
  rank: PropTypes.string.isRequired,
  suit: PropTypes.oneOf(['S', 'H', 'D', 'C']).isRequired,
  variant: PropTypes.oneOf(['correct', 'incorrect', '']),
};

/**
 * DefensiveSignal - Main component
 */
function DefensiveSignal({ onComplete = null, onClose = null }) {
  // Flow state
  const [flowState, setFlowState] = useState(STATES.LEVEL_SELECT);

  // Quiz state
  const [situations, setSituations] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [decisions, setDecisions] = useState([]);
  const [selectedCardIndex, setSelectedCardIndex] = useState(-1);
  const [currentResult, setCurrentResult] = useState(null);

  // Get current situation
  const currentSituation = situations[currentIndex] || null;

  // Sorted hand for display
  const sortedHand = useMemo(() => {
    if (!currentSituation) return [];
    return sortCards(currentSituation.yourHand);
  }, [currentSituation]);

  // Disabled indices (cards not in signal suit)
  const disabledIndices = useMemo(() => {
    if (!currentSituation) return [];
    const signalSuit = currentSituation.signalSuit;
    return sortedHand
      .map((card, index) => (card.suit !== signalSuit ? index : -1))
      .filter((i) => i !== -1);
  }, [currentSituation, sortedHand]);

  // Handle level selection
  const handleLevelSelect = useCallback((level) => {
    let selected;
    if (level === 0) {
      // Mixed - all 8 situations shuffled
      selected = getShuffledSituations();
    } else {
      // Specific type
      selected = getSituationsByLevel(level);
    }
    setSituations(selected);
    setCurrentIndex(0);
    setDecisions([]);
    setSelectedCardIndex(-1);
    setCurrentResult(null);
    setFlowState(STATES.PRESENT);

    // Auto-transition to SELECT_CARD after brief display
    setTimeout(() => {
      setFlowState(STATES.SELECT_CARD);
    }, 800);
  }, []);

  // Handle card selection
  const handleCardClick = useCallback(
    (index) => {
      if (flowState !== STATES.SELECT_CARD) return;
      if (disabledIndices.includes(index)) return;

      const selectedCard = sortedHand[index];
      const result = evaluateSignal(currentSituation, selectedCard.rank);

      setSelectedCardIndex(index);
      setCurrentResult(result);

      // Record decision
      const decision = {
        situation: currentSituation,
        selectedRank: selectedCard.rank,
        result,
      };
      setDecisions((prev) => [...prev, decision]);

      setFlowState(STATES.RESULT);
    },
    [flowState, disabledIndices, sortedHand, currentSituation]
  );

  // Handle continue to next question or summary
  const handleContinue = useCallback(() => {
    if (currentIndex < situations.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedCardIndex(-1);
      setCurrentResult(null);
      setFlowState(STATES.PRESENT);

      // Auto-transition to SELECT_CARD
      setTimeout(() => {
        setFlowState(STATES.SELECT_CARD);
      }, 500);
    } else {
      // End of session
      setFlowState(STATES.SESSION_SUMMARY);
    }
  }, [currentIndex, situations.length]);

  // Handle finish
  const handleFinish = useCallback(() => {
    if (onComplete) {
      const flowResult = buildFlowResult(decisions);
      onComplete(flowResult);
    }
    if (onClose) {
      onClose();
    }
  }, [onComplete, onClose, decisions]);

  // Handle restart
  const handleRestart = useCallback(() => {
    setFlowState(STATES.LEVEL_SELECT);
    setSituations([]);
    setCurrentIndex(0);
    setDecisions([]);
    setSelectedCardIndex(-1);
    setCurrentResult(null);
  }, []);

  // Calculate summary for SESSION_SUMMARY state
  const summary = useMemo(() => {
    if (decisions.length === 0) return null;
    return calculateSummary(decisions);
  }, [decisions]);

  // Determine correct/incorrect indices for HandDisplay
  const correctIndex = useMemo(() => {
    if (flowState !== STATES.RESULT || !currentResult) return -1;
    if (currentResult.isCorrect) return selectedCardIndex;
    // Find the correct card index
    return sortedHand.findIndex((c) => c.rank === currentResult.correctCard);
  }, [flowState, currentResult, selectedCardIndex, sortedHand]);

  const incorrectIndex = useMemo(() => {
    if (flowState !== STATES.RESULT || !currentResult) return -1;
    if (currentResult.isCorrect) return -1;
    return selectedCardIndex;
  }, [flowState, currentResult, selectedCardIndex]);

  // Render LEVEL_SELECT state
  const renderLevelSelect = () => (
    <div className="signal-level-select">
      <h2 className="signal-level-title">Defensive Signals Quiz</h2>
      <p className="signal-level-subtitle">Choose a signal type to practice</p>
      <div className="signal-level-buttons">
        {LEVEL_OPTIONS.map((opt) => (
          <button
            key={opt.level}
            className="signal-level-btn"
            onClick={() => handleLevelSelect(opt.level)}
            type="button"
          >
            <span className="signal-level-btn-name">{opt.name}</span>
            <span className="signal-level-btn-desc">{opt.desc}</span>
          </button>
        ))}
      </div>
    </div>
  );

  // Render felt content (situation + hand)
  const renderFeltContent = () => {
    if (!currentSituation) return null;

    const signalSuitSymbol = SUIT_SYMBOLS[currentSituation.signalSuit];
    const signalInfo = SIGNAL_TYPE_INFO[currentSituation.signalType];

    return (
      <div className="signal-felt-content">
        {/* Situation Panel */}
        <div className="signal-situation-panel">
          <div className="signal-situation-box">
            <h3 className="signal-situation-title">Situation</h3>
            <div className="signal-situation-line">
              <span className="signal-situation-label">Contract:</span>
              <span className="signal-situation-value">
                {currentSituation.contract}
              </span>
            </div>
            <div className="signal-situation-line">
              <span className="signal-situation-label">Partner leads:</span>
              <span className="signal-situation-value">
                {currentSituation.partnerLead.charAt(0) === 'H'
                  ? SUIT_SYMBOLS.H
                  : currentSituation.partnerLead.charAt(0) === 'S'
                    ? SUIT_SYMBOLS.S
                    : currentSituation.partnerLead.charAt(0) === 'D'
                      ? SUIT_SYMBOLS.D
                      : SUIT_SYMBOLS.C}
                {currentSituation.partnerLead.substring(1)}
              </span>
            </div>

            <div className="signal-dummy-section">
              <div className="signal-dummy-label">Dummy</div>
              <DummyDiagram cards={currentSituation.dummy} />
            </div>
          </div>
        </div>

        {/* Your Hand Panel */}
        <div className="signal-your-hand-panel">
          <div className="signal-your-hand-box">
            <h3 className="signal-your-hand-title">Your Hand</h3>
            <div className="signal-hand-container">
              <HandDisplay
                cards={sortedHand}
                mode="hand-h"
                selectable={flowState === STATES.SELECT_CARD}
                selectedIndex={selectedCardIndex}
                correctIndex={correctIndex}
                incorrectIndex={incorrectIndex}
                disabledIndices={disabledIndices}
                onCardClick={handleCardClick}
              />
            </div>
            <div className="signal-suit-indicator">
              <span className="signal-suit-symbol">{signalSuitSymbol}</span>
              <span>Signal in {signalInfo.name}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render interaction content based on state
  const renderInteractionContent = () => {
    if (flowState === STATES.LEVEL_SELECT) {
      return null; // Level select shown in felt zone
    }

    if (flowState === STATES.PRESENT || flowState === STATES.SELECT_CARD) {
      const signalInfo = SIGNAL_TYPE_INFO[currentSituation?.signalType];
      return (
        <div className="signal-interaction-content">
          <span className="signal-type-badge">{signalInfo?.name} Signal</span>
          <p className="signal-prompt">{currentSituation?.prompt}</p>
          {flowState === STATES.SELECT_CARD && (
            <p className="signal-waiting-text">
              Click a card in the signal suit
            </p>
          )}
        </div>
      );
    }

    if (flowState === STATES.RESULT && currentResult) {
      const signalSuit = currentSituation?.signalSuit;
      return (
        <div className="signal-result-content">
          <ResultStrip
            type={currentResult.isCorrect ? 'success' : 'error'}
            message={
              currentResult.isCorrect
                ? currentResult.isExactlyCorrect
                  ? 'Correct!'
                  : 'Acceptable signal'
                : 'Incorrect signal'
            }
          />
          <p className="signal-explanation">{currentResult.explanation}</p>

          {!currentResult.isExactlyCorrect && (
            <div className="signal-result-cards">
              <div className="signal-card-label">
                <span className="signal-card-label-text">You played</span>
                <CardDisplay
                  rank={currentResult.selectedRank}
                  suit={signalSuit}
                  variant={currentResult.isCorrect ? '' : 'incorrect'}
                />
              </div>
              <div className="signal-card-label">
                <span className="signal-card-label-text">Best card</span>
                <CardDisplay
                  rank={currentResult.correctCard}
                  suit={signalSuit}
                  variant="correct"
                />
              </div>
            </div>
          )}

          <PrimaryButton onClick={handleContinue}>
            {currentIndex < situations.length - 1
              ? 'Next Question'
              : 'View Results'}
          </PrimaryButton>
        </div>
      );
    }

    if (flowState === STATES.SESSION_SUMMARY && summary) {
      return (
        <div className="signal-summary">
          <div className="signal-summary-score">
            <div className="signal-summary-fraction">
              {summary.totalCorrect} / {summary.totalQuestions}
            </div>
            <div className="signal-summary-label">
              {summary.overallScore}% Correct
            </div>
          </div>

          <div className="signal-summary-breakdown">
            <div className="signal-summary-breakdown-title">By Signal Type</div>
            {Object.entries(summary.byType).map(([type, stats]) => (
              <div key={type} className="signal-summary-type-row">
                <span className="signal-summary-type-name">
                  {SIGNAL_TYPE_INFO[type].name}
                </span>
                <span
                  className={`signal-summary-type-score ${getPerformanceClass(stats.accuracy)}`}
                >
                  {stats.accuracy !== null
                    ? `${stats.correct}/${stats.total} (${stats.accuracy}%)`
                    : '\u2014'}
                </span>
              </div>
            ))}
          </div>

          <div className="signal-summary-actions">
            <SecondaryButton onClick={handleRestart}>
              Practice Again
            </SecondaryButton>
            <PrimaryButton onClick={handleFinish}>Done</PrimaryButton>
          </div>
        </div>
      );
    }

    return null;
  };

  // Build step indicator
  const stepIndicator =
    flowState !== STATES.LEVEL_SELECT && flowState !== STATES.SESSION_SUMMARY
      ? `Question ${currentIndex + 1} of ${situations.length}`
      : undefined;

  // Render
  return (
    <FlowLayout
      title="Defensive Signals"
      stepIndicator={stepIndicator}
      onClose={onClose}
      feltContent={
        flowState === STATES.LEVEL_SELECT
          ? renderLevelSelect()
          : flowState !== STATES.SESSION_SUMMARY
            ? renderFeltContent()
            : null
      }
      interactionContent={renderInteractionContent()}
    />
  );
}

DefensiveSignal.propTypes = {
  /** Callback when flow completes with FlowResult */
  onComplete: PropTypes.func,
  /** Callback to close the flow */
  onClose: PropTypes.func,
};

export default DefensiveSignal;
