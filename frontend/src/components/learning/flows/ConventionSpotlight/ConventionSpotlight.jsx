/**
 * ConventionSpotlight.jsx
 *
 * Flow 9: Convention Spotlight
 * Provides a focused learning experience for bridge conventions with:
 * - Convention library with mastery tracking
 * - Quick reference cards
 * - Drill hands for practice
 * - Progress summaries
 *
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

import React, { useReducer, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

// Shared components
import {
  FlowLayout,
  HandDiagram,
  ChoiceGrid,
  ResultStrip,
  ProgressRing,
  SkillBar,
  PrimaryButton,
  SecondaryButton,
  BidTable,
} from '../../shared';

// Local imports
import { CONVENTIONS, QUESTION_TYPES, getConventionById } from './conventions.data';
import {
  FLOW_STATES,
  INITIAL_STATE,
  evaluateAnswer,
  createDecision,
  generateFlowResult,
  getSessionSummary,
  formatTimeSpent,
  hasMoreHands,
  getYesNoChoices,
  getRelatedConventions,
  flowReducer,
} from './ConventionSpotlight.logic';
import './ConventionSpotlight.css';

/**
 * ConventionLibrary - Grid of convention cards
 */
const ConventionLibrary = ({ conventions, masteryData, onSelectConvention }) => {
  return (
    <div className="convention-library">
      <div className="convention-library-header">
        <h2 className="convention-library-title">Convention Library</h2>
        <p className="convention-library-subtitle">
          Select a convention to study and practice
        </p>
      </div>
      <div className="convention-grid">
        {conventions.map((convention) => {
          const mastery = masteryData[convention.id] || 0;
          const masteryLevel = mastery >= 80 ? 'mastered' : mastery >= 60 ? 'learning' : 'needs-practice';

          return (
            <button
              key={convention.id}
              className="convention-card"
              onClick={() => onSelectConvention(convention)}
              type="button"
            >
              <div className="convention-card-header">
                <h3 className="convention-card-name">{convention.name}</h3>
                <span className="convention-card-category">
                  {convention.category}
                </span>
              </div>
              <div className="convention-card-mastery">
                <div className="mastery-bar">
                  <div
                    className={`mastery-fill ${masteryLevel}`}
                    style={{ width: `${mastery}%` }}
                  />
                </div>
                <span className="mastery-percent">{mastery}%</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

ConventionLibrary.propTypes = {
  conventions: PropTypes.array.isRequired,
  masteryData: PropTypes.object.isRequired,
  onSelectConvention: PropTypes.func.isRequired,
};

/**
 * ConventionReference - Quick reference card for a convention
 */
const ConventionReference = ({ convention, onBack, onStartDrill }) => {
  const { quickRef } = convention;

  return (
    <div className="convention-reference">
      <div className="reference-card">
        <div className="reference-header">
          <button
            className="reference-back-btn"
            onClick={onBack}
            type="button"
            aria-label="Back to library"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <h2 className="reference-title">{convention.name}</h2>
        </div>

        <div className="reference-section">
          <h3 className="reference-section-title">When to Use</h3>
          <p className="reference-when-to-use">{quickRef.whenToUse}</p>
        </div>

        <div className="reference-section">
          <h3 className="reference-section-title">Structure</h3>
          <code className="reference-structure">{quickRef.structure}</code>
        </div>

        <div className="reference-section">
          <h3 className="reference-section-title">Responses</h3>
          <ul className="reference-list">
            {quickRef.responses.map((response, idx) => (
              <li key={idx}>{response}</li>
            ))}
          </ul>
        </div>

        <div className="reference-section">
          <h3 className="reference-section-title">Key Points</h3>
          <ul className="reference-list">
            {quickRef.keyPoints.map((point, idx) => (
              <li key={idx}>{point}</li>
            ))}
          </ul>
        </div>

        <div className="reference-actions">
          <PrimaryButton onClick={onStartDrill}>
            Start Drill
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
};

ConventionReference.propTypes = {
  convention: PropTypes.object.isRequired,
  onBack: PropTypes.func.isRequired,
  onStartDrill: PropTypes.func.isRequired,
};

/**
 * DrillView - Hand practice with question
 */
const DrillView = ({
  convention,
  drillHand,
  handIndex,
  totalHands,
  selectedAnswer,
  showResult,
  onSelectAnswer,
  onSubmit,
}) => {
  const { questionType, question, choices } = drillHand;

  // Get choices based on question type
  const displayChoices = useMemo(() => {
    if (questionType === QUESTION_TYPES.YES_NO) {
      return getYesNoChoices();
    }
    return choices || [];
  }, [questionType, choices]);

  // Convert to ChoiceGrid format
  const choiceGridItems = displayChoices.map((choice) => ({
    id: choice.id,
    label: choice.label,
  }));

  const handleSelect = useCallback((choiceId) => {
    if (!showResult) {
      onSelectAnswer(choiceId);
    }
  }, [showResult, onSelectAnswer]);

  return (
    <>
      {/* Felt Zone Content */}
      <div className="drill-felt-content">
        <div className="drill-hand-section">
          <span className="drill-hand-label">Your Hand</span>
          <HandDiagram cards={drillHand.hand} highlight />
        </div>

        {drillHand.auctionSoFar && drillHand.auctionSoFar.length > 0 && (
          <div className="drill-auction-section">
            <div className="drill-auction-label">Auction So Far</div>
            <BidTable
              bids={drillHand.auctionSoFar}
              dealer="N"
              playerSeat="S"
            />
          </div>
        )}
      </div>

      {/* Interaction Zone Content */}
      <div className="drill-interaction">
        <p className="drill-question">{question}</p>

        <div className="drill-choices">
          <div className={questionType === QUESTION_TYPES.YES_NO ? 'drill-yes-no-choices' : 'drill-bid-choices'}>
            <ChoiceGrid
              choices={choiceGridItems}
              selectedId={selectedAnswer}
              correctId={showResult ? drillHand.correctAnswer : null}
              showResult={showResult}
              disabled={showResult}
              onSelect={handleSelect}
            />
          </div>

          {!showResult && selectedAnswer && (
            <PrimaryButton onClick={onSubmit}>
              Submit Answer
            </PrimaryButton>
          )}
        </div>
      </div>
    </>
  );
};

DrillView.propTypes = {
  convention: PropTypes.object.isRequired,
  drillHand: PropTypes.object.isRequired,
  handIndex: PropTypes.number.isRequired,
  totalHands: PropTypes.number.isRequired,
  selectedAnswer: PropTypes.string,
  showResult: PropTypes.bool.isRequired,
  onSelectAnswer: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
};

/**
 * FeedbackView - Result display after answering
 */
const FeedbackView = ({
  drillHand,
  isCorrect,
  hasNext,
  onNext,
  onShowSummary,
}) => {
  return (
    <div className="feedback-container">
      <ResultStrip
        type={isCorrect ? 'success' : 'error'}
        message={isCorrect ? 'Correct!' : 'Not quite right'}
      />

      <div className="feedback-explanation">
        {drillHand.explanation}
      </div>

      <div className="feedback-actions">
        {hasNext ? (
          <PrimaryButton onClick={onNext}>
            Next Question
          </PrimaryButton>
        ) : (
          <PrimaryButton onClick={onShowSummary}>
            See Summary
          </PrimaryButton>
        )}
      </div>
    </div>
  );
};

FeedbackView.propTypes = {
  drillHand: PropTypes.object.isRequired,
  isCorrect: PropTypes.bool.isRequired,
  hasNext: PropTypes.bool.isRequired,
  onNext: PropTypes.func.isRequired,
  onShowSummary: PropTypes.func.isRequired,
};

/**
 * ConventionSummaryView - Session summary
 */
const ConventionSummaryView = ({
  convention,
  decisions,
  timeSpent,
  relatedConventions,
  onPracticeAgain,
  onTryRelated,
  onBackToLibrary,
}) => {
  const summary = getSessionSummary(decisions);
  const masteryLabels = {
    'mastered': 'Mastered',
    'learning': 'Learning',
    'needs-practice': 'Needs Practice',
  };

  return (
    <div className="convention-summary">
      <div className="summary-header">
        <h2 className="summary-title">Session Complete!</h2>
        <p className="summary-convention-name">{convention.name}</p>
      </div>

      <div className="summary-progress">
        <ProgressRing
          percentage={summary.accuracy}
          size={100}
          strokeWidth={8}
        />
      </div>

      <div className="summary-stats">
        <div className="summary-stat">
          <span className="summary-stat-value correct">{summary.correct}</span>
          <span className="summary-stat-label">Correct</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-value incorrect">{summary.incorrect}</span>
          <span className="summary-stat-label">Incorrect</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-value">{formatTimeSpent(timeSpent)}</span>
          <span className="summary-stat-label">Time</span>
        </div>
      </div>

      <div className="summary-mastery">
        <p className="summary-mastery-label">Convention Status</p>
        <span className={`summary-mastery-level ${summary.masteryLevel}`}>
          {masteryLabels[summary.masteryLevel]}
        </span>
      </div>

      {relatedConventions.length > 0 && (
        <div className="summary-related">
          <h3 className="summary-related-title">Related Conventions</h3>
          <div className="summary-related-list">
            {relatedConventions.map((convId) => {
              const conv = getConventionById(convId);
              return conv ? (
                <button
                  key={convId}
                  className="summary-related-item"
                  onClick={() => onTryRelated(conv)}
                  type="button"
                >
                  {conv.name}
                </button>
              ) : null;
            })}
          </div>
        </div>
      )}

      <div className="summary-actions">
        <PrimaryButton onClick={onPracticeAgain}>
          Practice Again
        </PrimaryButton>
        <SecondaryButton onClick={onBackToLibrary}>
          Back to Library
        </SecondaryButton>
      </div>
    </div>
  );
};

ConventionSummaryView.propTypes = {
  convention: PropTypes.object.isRequired,
  decisions: PropTypes.array.isRequired,
  timeSpent: PropTypes.number.isRequired,
  relatedConventions: PropTypes.array.isRequired,
  onPracticeAgain: PropTypes.func.isRequired,
  onTryRelated: PropTypes.func.isRequired,
  onBackToLibrary: PropTypes.func.isRequired,
};

/**
 * ConventionSpotlight - Main component
 */
const ConventionSpotlight = ({
  onClose = null,
  onFlowComplete = null,
  masteryData = {},
}) => {
  const [state, dispatch] = useReducer(flowReducer, {
    ...INITIAL_STATE,
    startTime: Date.now(),
  });

  const {
    flowState,
    selectedConvention,
    currentHandIndex,
    selectedAnswer,
    showResult,
    decisions,
    conventionStartTime,
  } = state;

  // Get current drill hand
  const currentDrillHand = useMemo(() => {
    if (!selectedConvention) return null;
    return selectedConvention.drillHands[currentHandIndex];
  }, [selectedConvention, currentHandIndex]);

  // Get related conventions for summary
  const relatedConventions = useMemo(() => {
    if (!selectedConvention) return [];
    return getRelatedConventions(selectedConvention.id, CONVENTIONS);
  }, [selectedConvention]);

  // Handlers
  const handleSelectConvention = useCallback((convention) => {
    dispatch({ type: 'SELECT_CONVENTION', convention });
  }, []);

  const handleBackToLibrary = useCallback(() => {
    dispatch({ type: 'BACK_TO_LIBRARY' });
  }, []);

  const handleBackToReference = useCallback(() => {
    dispatch({ type: 'BACK_TO_REFERENCE' });
  }, []);

  const handleStartDrill = useCallback(() => {
    dispatch({ type: 'START_DRILL' });
  }, []);

  const handleSelectAnswer = useCallback((answer) => {
    dispatch({ type: 'SELECT_ANSWER', answer });
  }, []);

  const handleSubmitAnswer = useCallback(() => {
    if (!currentDrillHand || !selectedAnswer) return;

    const isCorrect = evaluateAnswer(currentDrillHand, selectedAnswer);
    const decision = createDecision(
      currentDrillHand,
      selectedConvention.id,
      currentHandIndex,
      selectedAnswer,
      isCorrect
    );

    dispatch({ type: 'SUBMIT_ANSWER', decision });
  }, [currentDrillHand, selectedAnswer, selectedConvention, currentHandIndex]);

  const handleNextHand = useCallback(() => {
    dispatch({ type: 'NEXT_HAND' });
  }, []);

  const handleShowSummary = useCallback(() => {
    dispatch({ type: 'SHOW_SUMMARY' });

    // Generate and emit flow result
    if (onFlowComplete && selectedConvention) {
      const timeSpent = Date.now() - (conventionStartTime || Date.now());
      const result = generateFlowResult(selectedConvention.id, decisions, timeSpent);
      onFlowComplete(result);
    }
  }, [onFlowComplete, selectedConvention, conventionStartTime, decisions]);

  const handlePracticeAgain = useCallback(() => {
    dispatch({ type: 'START_DRILL' });
  }, []);

  const handleTryRelated = useCallback((convention) => {
    dispatch({ type: 'SELECT_CONVENTION', convention });
  }, []);

  // Render based on flow state
  const renderContent = () => {
    switch (flowState) {
      case FLOW_STATES.LIBRARY:
        return {
          title: 'Convention Spotlight',
          feltContent: null,
          interactionContent: (
            <ConventionLibrary
              conventions={CONVENTIONS}
              masteryData={masteryData}
              onSelectConvention={handleSelectConvention}
            />
          ),
        };

      case FLOW_STATES.REFERENCE:
        return {
          title: selectedConvention?.name || 'Convention',
          feltContent: null,
          interactionContent: (
            <ConventionReference
              convention={selectedConvention}
              onBack={handleBackToLibrary}
              onStartDrill={handleStartDrill}
            />
          ),
        };

      case FLOW_STATES.DRILL:
      case FLOW_STATES.FEEDBACK:
        const totalHands = selectedConvention?.drillHands.length || 0;
        const stepIndicator = `Question ${currentHandIndex + 1} of ${totalHands}`;
        const isLastDecisionCorrect = decisions.length > 0
          ? decisions[decisions.length - 1].isCorrect
          : false;

        if (flowState === FLOW_STATES.DRILL) {
          return {
            title: selectedConvention?.name || 'Drill',
            stepIndicator,
            feltContent: currentDrillHand ? (
              <DrillView
                convention={selectedConvention}
                drillHand={currentDrillHand}
                handIndex={currentHandIndex}
                totalHands={totalHands}
                selectedAnswer={selectedAnswer}
                showResult={false}
                onSelectAnswer={handleSelectAnswer}
                onSubmit={handleSubmitAnswer}
              />
            ) : null,
            interactionContent: null,
          };
        }

        // FEEDBACK state
        return {
          title: selectedConvention?.name || 'Drill',
          stepIndicator,
          feltContent: currentDrillHand ? (
            <>
              <div className="drill-hand-section">
                <span className="drill-hand-label">Your Hand</span>
                <HandDiagram cards={currentDrillHand.hand} highlight />
              </div>
              {currentDrillHand.auctionSoFar && currentDrillHand.auctionSoFar.length > 0 && (
                <div className="drill-auction-section">
                  <div className="drill-auction-label">Auction So Far</div>
                  <BidTable
                    bids={currentDrillHand.auctionSoFar}
                    dealer="N"
                    playerSeat="S"
                  />
                </div>
              )}
            </>
          ) : null,
          interactionContent: currentDrillHand ? (
            <FeedbackView
              drillHand={currentDrillHand}
              isCorrect={isLastDecisionCorrect}
              hasNext={hasMoreHands(currentHandIndex, totalHands)}
              onNext={handleNextHand}
              onShowSummary={handleShowSummary}
            />
          ) : null,
        };

      case FLOW_STATES.CONVENTION_SUMMARY:
        const timeSpent = Date.now() - (conventionStartTime || Date.now());
        return {
          title: 'Session Summary',
          feltContent: null,
          interactionContent: (
            <ConventionSummaryView
              convention={selectedConvention}
              decisions={decisions}
              timeSpent={timeSpent}
              relatedConventions={relatedConventions}
              onPracticeAgain={handlePracticeAgain}
              onTryRelated={handleTryRelated}
              onBackToLibrary={handleBackToLibrary}
            />
          ),
        };

      default:
        return {
          title: 'Convention Spotlight',
          feltContent: null,
          interactionContent: null,
        };
    }
  };

  const content = renderContent();

  // Determine if felt zone should be shown
  const showFeltZone = flowState === FLOW_STATES.DRILL || flowState === FLOW_STATES.FEEDBACK;

  return (
    <FlowLayout
      title={content.title}
      stepIndicator={content.stepIndicator}
      onClose={onClose}
      feltContent={showFeltZone ? (
        <div className="drill-felt-content">
          {content.feltContent}
        </div>
      ) : null}
      interactionContent={content.interactionContent}
    />
  );
};

ConventionSpotlight.propTypes = {
  onClose: PropTypes.func,
  onFlowComplete: PropTypes.func,
  masteryData: PropTypes.object,
};

export default ConventionSpotlight;
