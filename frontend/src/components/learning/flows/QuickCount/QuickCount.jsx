/**
 * QuickCount.jsx
 *
 * Quick Count Drill - Flow 5
 * A timed drill for practicing hand evaluation (HCP + distribution points).
 *
 * Flow States: LEVEL_SELECT -> COUNTDOWN -> SHOW_HAND -> ANSWER -> FEEDBACK -> ROUND_SUMMARY
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';

import {
  FlowLayout,
  HandDisplay,
  ResultStrip,
  PrimaryButton,
  SecondaryButton
} from '../../shared';

import { SUIT_SYMBOLS } from '../../types/hand-types';

import {
  LEVELS,
  LEVEL_NAMES,
  LEVEL_DESCRIPTIONS,
  HANDS_PER_ROUND,
  generateHandData,
  getPointBreakdown,
  formatTime,
  calculateAverageTime,
  calculateScorePercentage,
  getPerformanceRating
} from './QuickCount.logic';

import './QuickCount.css';

// Flow states
const STATES = {
  LEVEL_SELECT: 'LEVEL_SELECT',
  COUNTDOWN: 'COUNTDOWN',
  SHOW_HAND: 'SHOW_HAND',
  ANSWER: 'ANSWER',
  FEEDBACK: 'FEEDBACK',
  ROUND_SUMMARY: 'ROUND_SUMMARY'
};

/**
 * QuickCount - Main component for the Quick Count drill
 *
 * @param {function} onComplete - Callback with FlowResult when round completes
 * @param {function} onClose - Callback when user closes the flow
 * @param {number} initialLevel - Optional starting level (1-4)
 */
function QuickCount({ onComplete = null, onClose = null, initialLevel = null }) {
  // ============================================================================
  // State
  // ============================================================================

  const [flowState, setFlowState] = useState(
    initialLevel ? STATES.COUNTDOWN : STATES.LEVEL_SELECT
  );
  const [level, setLevel] = useState(initialLevel || LEVELS.HCP_ONLY);
  const [countdownValue, setCountdownValue] = useState(3);

  // Current hand data
  const [currentHandData, setCurrentHandData] = useState(null);

  // Round tracking
  const [roundNumber, setRoundNumber] = useState(1);
  const [handIndex, setHandIndex] = useState(0);
  const [roundResults, setRoundResults] = useState([]);

  // Timer
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);

  // Answer state
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isCorrect, setIsCorrect] = useState(null);

  // Personal best tracking (in localStorage)
  const [personalBest, setPersonalBest] = useState(() => {
    try {
      const saved = localStorage.getItem('quickCount_personalBest');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  // ============================================================================
  // Timer Functions
  // ============================================================================

  const startTimer = useCallback(() => {
    startTimeRef.current = Date.now();
    timerRef.current = setInterval(() => {
      setElapsedTime((Date.now() - startTimeRef.current) / 1000);
    }, 100);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // ============================================================================
  // Flow Actions
  // ============================================================================

  const handleLevelSelect = useCallback((selectedLevel) => {
    setLevel(selectedLevel);
    setFlowState(STATES.COUNTDOWN);
    setCountdownValue(3);
  }, []);

  // Countdown effect
  useEffect(() => {
    if (flowState !== STATES.COUNTDOWN) return;

    if (countdownValue > 0) {
      const timer = setTimeout(() => {
        setCountdownValue(countdownValue - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      // Countdown finished - start the round
      const handData = generateHandData(level, 0);
      setCurrentHandData(handData);
      setHandIndex(0);
      setRoundResults([]);
      setElapsedTime(0);
      setSelectedAnswer(null);
      setIsCorrect(null);
      setFlowState(STATES.SHOW_HAND);
      startTimer();
    }
  }, [flowState, countdownValue, level, startTimer]);

  const handleAnswerSelect = useCallback((choiceValue) => {
    if (flowState !== STATES.SHOW_HAND) return;

    stopTimer();
    setSelectedAnswer(choiceValue);
    const correct = choiceValue === currentHandData.correctAnswer;
    setIsCorrect(correct);
    setFlowState(STATES.ANSWER);

    // Brief pause then show feedback
    setTimeout(() => {
      setFlowState(STATES.FEEDBACK);
    }, 300);
  }, [flowState, currentHandData, stopTimer]);

  const handleContinue = useCallback(() => {
    // Record this hand's result
    const result = {
      handIndex,
      hand: currentHandData.hand,
      level: currentHandData.level,
      options: currentHandData.options,
      correctAnswer: currentHandData.correctAnswer,
      playerAnswer: selectedAnswer,
      isCorrect,
      time: elapsedTime
    };

    const newResults = [...roundResults, result];
    setRoundResults(newResults);

    const nextHandIndex = handIndex + 1;

    if (nextHandIndex >= HANDS_PER_ROUND) {
      // Round complete
      setFlowState(STATES.ROUND_SUMMARY);

      // Calculate and save personal best
      const correctCount = newResults.filter(r => r.isCorrect).length;
      const avgTime = calculateAverageTime(newResults.map(r => r.time));
      const levelKey = `level_${level}`;

      const currentBest = personalBest[levelKey] || { score: 0, avgTime: Infinity };
      const isNewBest = correctCount > currentBest.score ||
        (correctCount === currentBest.score && avgTime < currentBest.avgTime);

      if (isNewBest) {
        const newPersonalBest = {
          ...personalBest,
          [levelKey]: { score: correctCount, avgTime }
        };
        setPersonalBest(newPersonalBest);
        try {
          localStorage.setItem('quickCount_personalBest', JSON.stringify(newPersonalBest));
        } catch {
          // Ignore localStorage errors
        }
      }

      // Emit FlowResult
      if (onComplete) {
        const flowResult = {
          flowType: 'count',
          handId: `count-${level}-${roundNumber}`,
          timestamp: new Date().toISOString(),
          decisions: newResults.map((r, i) => ({
            decisionId: `count-${level}-${roundNumber}-${i}`,
            category: `point_counting_level_${level}`,
            playerAnswer: r.playerAnswer,
            correctAnswer: r.correctAnswer,
            isCorrect: r.isCorrect,
            timeSpent: r.time * 1000
          })),
          overallScore: calculateScorePercentage(correctCount, HANDS_PER_ROUND),
          timeSpent: newResults.reduce((sum, r) => sum + r.time * 1000, 0),
          conventionTags: []
        };
        onComplete(flowResult);
      }
    } else {
      // Next hand
      const handData = generateHandData(level, nextHandIndex);
      setCurrentHandData(handData);
      setHandIndex(nextHandIndex);
      setElapsedTime(0);
      setSelectedAnswer(null);
      setIsCorrect(null);
      setFlowState(STATES.SHOW_HAND);
      startTimer();
    }
  }, [
    handIndex, currentHandData, selectedAnswer, isCorrect, elapsedTime,
    roundResults, level, roundNumber, personalBest, onComplete, startTimer
  ]);

  const handlePlayAgain = useCallback(() => {
    setRoundNumber(roundNumber + 1);
    setFlowState(STATES.COUNTDOWN);
    setCountdownValue(3);
  }, [roundNumber]);

  const handleChangeLevel = useCallback(() => {
    setFlowState(STATES.LEVEL_SELECT);
  }, []);

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const renderLevelSelect = () => (
    <div className="quick-count-level-select">
      <h2>Choose Your Level</h2>
      <p>Practice counting points with increasing complexity</p>
      <div className="level-buttons">
        {Object.values(LEVELS).map((lvl) => (
          <button
            key={lvl}
            type="button"
            className="level-btn"
            onClick={() => handleLevelSelect(lvl)}
          >
            <span className="level-btn-title">
              Level {lvl}: {LEVEL_NAMES[lvl]}
            </span>
            <span className="level-btn-desc">
              {LEVEL_DESCRIPTIONS[lvl]}
            </span>
          </button>
        ))}
      </div>
    </div>
  );

  const renderCountdown = () => (
    <div className="quick-count-countdown">
      <span className="countdown-number" key={countdownValue}>
        {countdownValue > 0 ? countdownValue : 'Go!'}
      </span>
    </div>
  );

  const renderTimer = () => {
    const isStopped = flowState !== STATES.SHOW_HAND;
    return (
      <div className={`timer-display ${isStopped ? 'timer-stopped' : ''}`}>
        <span className="timer-icon">⏱</span>
        <span>{formatTime(elapsedTime)}s</span>
      </div>
    );
  };

  const renderHand = () => {
    if (!currentHandData) return null;
    return (
      <div className="quick-count-felt">
        {renderTimer()}
        <div className="hand-wrapper">
          <HandDisplay cards={currentHandData.hand} mode="hand-h" />
        </div>
      </div>
    );
  };

  const renderPrompt = () => {
    if (!currentHandData) return null;

    const { prompt, options } = currentHandData;

    // For Level 4, colorize the trump suit in the prompt
    if (level === LEVELS.DECLARER_VS_DUMMY && options.trumpSuit) {
      const trumpSymbol = SUIT_SYMBOLS[options.trumpSuit];
      const isRed = options.trumpSuit === 'H' || options.trumpSuit === 'D';
      const role = options.isDummy ? 'DUMMY' : 'DECLARER';

      return (
        <p className="question-prompt">
          You are <strong>{role}</strong>. Trump is{' '}
          <span className={`trump-suit ${isRed ? 'red' : 'black'}`}>
            {trumpSymbol}
          </span>
          . How many points?
        </p>
      );
    }

    return <p className="question-prompt">{prompt}</p>;
  };

  const renderChoices = () => {
    if (!currentHandData) return null;

    const showResult = flowState === STATES.ANSWER || flowState === STATES.FEEDBACK;

    return (
      <div className="quick-count-choices">
        {currentHandData.choices.map((choice) => {
          let className = 'count-choice-btn';

          if (showResult) {
            if (choice.value === currentHandData.correctAnswer) {
              className += ' correct';
            } else if (choice.value === selectedAnswer) {
              className += ' wrong';
            } else {
              className += ' dimmed';
            }
          } else if (choice.value === selectedAnswer) {
            className += ' selected';
          }

          return (
            <button
              key={choice.id}
              type="button"
              className={className}
              onClick={() => handleAnswerSelect(choice.value)}
              disabled={flowState !== STATES.SHOW_HAND}
              aria-pressed={choice.value === selectedAnswer}
            >
              {choice.label}
            </button>
          );
        })}
      </div>
    );
  };

  const renderQuestion = () => (
    <div className="quick-count-question">
      {renderPrompt()}
      {renderChoices()}
    </div>
  );

  const renderProgressDots = () => {
    const dots = [];
    for (let i = 0; i < HANDS_PER_ROUND; i++) {
      let className = 'progress-dot';
      if (i < roundResults.length) {
        className += roundResults[i].isCorrect ? ' correct' : ' wrong';
      }
      if (i === handIndex) {
        className += ' current';
      }
      dots.push(<span key={i} className={className} />);
    }
    return <div className="progress-dots">{dots}</div>;
  };

  const renderFeedback = () => {
    if (!currentHandData) return null;

    const breakdown = getPointBreakdown(
      currentHandData.hand,
      currentHandData.level,
      currentHandData.options
    );

    return (
      <div className="quick-count-feedback">
        <ResultStrip
          type={isCorrect ? 'success' : 'error'}
          message={isCorrect ? 'Correct!' : `Incorrect. The answer is ${currentHandData.correctAnswer}.`}
          detail={`Your answer: ${selectedAnswer}`}
        />
        <p className="breakdown-text">{breakdown}</p>
        {renderProgressDots()}
      </div>
    );
  };

  const renderSummary = () => {
    const correctCount = roundResults.filter(r => r.isCorrect).length;
    const avgTime = calculateAverageTime(roundResults.map(r => r.time));
    const percentage = calculateScorePercentage(correctCount, HANDS_PER_ROUND);
    const rating = getPerformanceRating(percentage);

    const levelKey = `level_${level}`;
    const best = personalBest[levelKey];
    const isNewBest = best &&
      (correctCount > (personalBest[levelKey]?.score || 0) ||
        (correctCount === best.score && avgTime <= best.avgTime));

    return (
      <div className="quick-count-summary">
        <h2 className="summary-title">Round Complete!</h2>

        <div className="summary-score">
          <span className={`summary-score-value ${rating}`}>
            {correctCount}/{HANDS_PER_ROUND}
          </span>
          <span className="summary-score-label">correct answers</span>
        </div>

        <div className="summary-stats">
          <div className="summary-stat">
            <span className="summary-stat-label">Accuracy</span>
            <span className="summary-stat-value">{percentage}%</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat-label">Average Time</span>
            <span className="summary-stat-value">{formatTime(avgTime)}s</span>
          </div>
          {best && (
            <div className="summary-stat">
              <span className="summary-stat-label">Personal Best</span>
              <span className={`summary-stat-value ${isNewBest ? 'is-best' : ''}`}>
                {best.score}/{HANDS_PER_ROUND} ({formatTime(best.avgTime)}s)
                {isNewBest && ' - NEW!'}
              </span>
            </div>
          )}
        </div>

        <div className="summary-actions">
          <PrimaryButton onClick={handlePlayAgain}>
            Play Again
          </PrimaryButton>
          <SecondaryButton onClick={handleChangeLevel}>
            Change Level
          </SecondaryButton>
        </div>
      </div>
    );
  };

  // ============================================================================
  // Main Render
  // ============================================================================

  const getStepIndicator = () => {
    if (flowState === STATES.LEVEL_SELECT || flowState === STATES.COUNTDOWN) {
      return null;
    }
    if (flowState === STATES.ROUND_SUMMARY) {
      return `Level ${level}`;
    }
    return `Hand ${handIndex + 1} of ${HANDS_PER_ROUND}`;
  };

  const getFeltContent = () => {
    switch (flowState) {
      case STATES.COUNTDOWN:
        return renderCountdown();
      case STATES.SHOW_HAND:
      case STATES.ANSWER:
      case STATES.FEEDBACK:
        return renderHand();
      default:
        return null;
    }
  };

  const getInteractionContent = () => {
    switch (flowState) {
      case STATES.LEVEL_SELECT:
        return renderLevelSelect();
      case STATES.SHOW_HAND:
        return renderQuestion();
      case STATES.ANSWER:
        return renderQuestion();
      case STATES.FEEDBACK:
        return renderFeedback();
      case STATES.ROUND_SUMMARY:
        return renderSummary();
      default:
        return null;
    }
  };

  const getActionContent = () => {
    if (flowState === STATES.FEEDBACK) {
      return (
        <PrimaryButton onClick={handleContinue}>
          {handIndex + 1 >= HANDS_PER_ROUND ? 'See Results' : 'Next Hand'}
        </PrimaryButton>
      );
    }
    return null;
  };

  return (
    <FlowLayout
      title="Quick Count"
      stepIndicator={getStepIndicator()}
      onClose={onClose}
      feltContent={getFeltContent()}
      interactionContent={getInteractionContent()}
      actionContent={getActionContent()}
    />
  );
}

QuickCount.propTypes = {
  onComplete: PropTypes.func,
  onClose: PropTypes.func,
  initialLevel: PropTypes.oneOf([1, 2, 3, 4])
};

export default QuickCount;
