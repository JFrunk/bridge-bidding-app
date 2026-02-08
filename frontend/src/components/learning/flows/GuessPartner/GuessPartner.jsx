/**
 * GuessPartner.jsx
 *
 * Main component for the Guess Partner's Hand learning flow.
 * Player sees their hand and the completed auction, then estimates
 * partner's hand characteristics (HCP, longest suit, length, shape).
 *
 * Flow States: PRESENT -> ESTIMATE -> REVEAL -> SCORE
 *
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  FlowLayout,
  HandDisplay,
  HandDiagram,
  BidTable,
  RangeSlider,
  ResultStrip,
  ScoreRow,
  PrimaryButton,
  SecondaryButton,
} from '../../shared';
import { generateHandId } from '../../types/flow-types';
import { SUIT_SYMBOLS } from '../../types/hand-types';
import {
  FLOW_STATES,
  SHAPE_TYPES,
  getInitialEstimates,
  areEstimatesComplete,
  scoreAllEstimates,
  generateFlowResult,
  calculateHCP,
  findLongestSuits,
} from './GuessPartner.logic';
import { getRandomScenario } from './mockData';
import './GuessPartner.css';

/**
 * Suit choice button component
 */
const SuitChoiceButton = ({ suit, selected, correct, wrong, disabled, onClick }) => {
  const suitNames = { S: 'spades', H: 'hearts', D: 'diamonds', C: 'clubs' };

  const classes = [
    'suit-choice-btn',
    selected ? 'selected' : '',
    correct ? 'correct' : '',
    wrong ? 'wrong' : '',
    disabled ? 'disabled' : '',
  ].filter(Boolean).join(' ');

  return (
    <button
      type="button"
      className={classes}
      onClick={() => onClick(suit)}
      disabled={disabled}
      aria-pressed={selected}
      aria-label={`${suitNames[suit]}`}
    >
      <span className={`suit-symbol ${suitNames[suit]}`}>
        {SUIT_SYMBOLS[suit]}
      </span>
    </button>
  );
};

SuitChoiceButton.propTypes = {
  suit: PropTypes.oneOf(['S', 'H', 'D', 'C']).isRequired,
  selected: PropTypes.bool,
  correct: PropTypes.bool,
  wrong: PropTypes.bool,
  disabled: PropTypes.bool,
  onClick: PropTypes.func.isRequired,
};

/**
 * Length choice button component
 */
const LengthChoiceButton = ({ length, label, selected, correct, wrong, disabled, onClick }) => {
  const classes = [
    'length-choice-btn',
    selected ? 'selected' : '',
    correct ? 'correct' : '',
    wrong ? 'wrong' : '',
    disabled ? 'disabled' : '',
  ].filter(Boolean).join(' ');

  return (
    <button
      type="button"
      className={classes}
      onClick={() => onClick(length)}
      disabled={disabled}
      aria-pressed={selected}
    >
      {label}
    </button>
  );
};

LengthChoiceButton.propTypes = {
  length: PropTypes.number.isRequired,
  label: PropTypes.string.isRequired,
  selected: PropTypes.bool,
  correct: PropTypes.bool,
  wrong: PropTypes.bool,
  disabled: PropTypes.bool,
  onClick: PropTypes.func.isRequired,
};

/**
 * Shape choice button component
 */
const ShapeChoiceButton = ({ shape, label, selected, correct, wrong, disabled, onClick }) => {
  const classes = [
    'shape-choice-btn',
    selected ? 'selected' : '',
    correct ? 'correct' : '',
    wrong ? 'wrong' : '',
    disabled ? 'disabled' : '',
  ].filter(Boolean).join(' ');

  return (
    <button
      type="button"
      className={classes}
      onClick={() => onClick(shape)}
      disabled={disabled}
      aria-pressed={selected}
    >
      {label}
    </button>
  );
};

ShapeChoiceButton.propTypes = {
  shape: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  selected: PropTypes.bool,
  correct: PropTypes.bool,
  wrong: PropTypes.bool,
  disabled: PropTypes.bool,
  onClick: PropTypes.func.isRequired,
};

/**
 * GuessPartner - Main flow component
 */
function GuessPartner({ onComplete = null, onClose = null, initialScenario = null }) {
  // Flow state
  const [flowState, setFlowState] = useState(FLOW_STATES.PRESENT);
  const [startTime] = useState(Date.now());

  // Scenario data
  const [scenario, setScenario] = useState(() => initialScenario || getRandomScenario());
  const [handId] = useState(() => generateHandId());

  // Estimation state
  const [estimates, setEstimates] = useState(getInitialEstimates());

  // Scoring results
  const [results, setResults] = useState(null);

  // Get player's hand (South) and partner's hand (North)
  const playerHand = useMemo(() => scenario.hands.south, [scenario]);
  const partnerHand = useMemo(() => scenario.hands.north, [scenario]);

  // Calculate partner's actual values for comparison
  const partnerActuals = useMemo(() => {
    const hcp = calculateHCP(partnerHand);
    const { suits, length } = findLongestSuits(partnerHand);
    return { hcp, longestSuits: suits, longestLength: length };
  }, [partnerHand]);

  // Update HCP range
  const handleHCPChange = useCallback(({ low, high }) => {
    setEstimates(prev => ({
      ...prev,
      hcpRange: { low, high },
    }));
  }, []);

  // Update longest suit selection
  const handleSuitSelect = useCallback((suit) => {
    setEstimates(prev => ({
      ...prev,
      longestSuit: suit,
    }));
  }, []);

  // Update suit length selection
  const handleLengthSelect = useCallback((length) => {
    setEstimates(prev => ({
      ...prev,
      suitLength: length,
    }));
  }, []);

  // Update shape selection
  const handleShapeSelect = useCallback((shape) => {
    setEstimates(prev => ({
      ...prev,
      shape: shape,
    }));
  }, []);

  // Advance from PRESENT to ESTIMATE
  const handleBeginEstimate = useCallback(() => {
    setFlowState(FLOW_STATES.ESTIMATE);
  }, []);

  // Reveal partner's hand and score
  const handleReveal = useCallback(() => {
    const scoringResults = scoreAllEstimates(estimates, partnerHand);
    setResults(scoringResults);
    setFlowState(FLOW_STATES.REVEAL);
  }, [estimates, partnerHand]);

  // Move from REVEAL to SCORE
  const handleShowScore = useCallback(() => {
    setFlowState(FLOW_STATES.SCORE);
  }, []);

  // Complete the flow and emit result
  const handleNextHand = useCallback(() => {
    if (results && onComplete) {
      const timeSpent = Date.now() - startTime;
      const flowResult = generateFlowResult(
        handId,
        results.decisions,
        results.overallScore,
        timeSpent
      );
      onComplete(flowResult);
    }

    // Load next scenario
    setScenario(getRandomScenario());
    setEstimates(getInitialEstimates());
    setResults(null);
    setFlowState(FLOW_STATES.PRESENT);
  }, [results, onComplete, handId, startTime]);

  // Check if estimates are complete for reveal button
  const canReveal = useMemo(() => areEstimatesComplete(estimates), [estimates]);

  // Get step indicator text
  const getStepIndicator = () => {
    switch (flowState) {
      case FLOW_STATES.PRESENT:
        return 'Step 1 of 4: Review';
      case FLOW_STATES.ESTIMATE:
        return 'Step 2 of 4: Estimate';
      case FLOW_STATES.REVEAL:
        return 'Step 3 of 4: Reveal';
      case FLOW_STATES.SCORE:
        return 'Step 4 of 4: Score';
      default:
        return '';
    }
  };

  // Get overall score rating
  const getScoreRating = (score) => {
    if (score >= 75) return 'excellent';
    if (score >= 50) return 'good';
    return 'poor';
  };

  // Render felt zone content based on state
  const renderFeltContent = () => {
    return (
      <div className="guess-partner-felt">
        {/* Auction display */}
        <div className="auction-section">
          <div className="felt-section-label">Auction</div>
          <BidTable
            bids={scenario.auction}
            dealer={scenario.dealer}
            playerSeat="S"
          />
        </div>

        {/* Player's hand */}
        <div className="hand-section">
          <div className="felt-section-label">Your Hand (South)</div>
          <HandDisplay cards={playerHand} mode="hand-h" />
        </div>

        {/* Partner's hand (shown in REVEAL and SCORE states) */}
        {(flowState === FLOW_STATES.REVEAL || flowState === FLOW_STATES.SCORE) && (
          <div className="partner-hand-section">
            <div className="partner-hand-label">Partner's Hand (North)</div>
            <HandDiagram cards={partnerHand} highlight />
          </div>
        )}
      </div>
    );
  };

  // Render interaction zone content based on state
  const renderInteractionContent = () => {
    switch (flowState) {
      case FLOW_STATES.PRESENT:
        return (
          <div className="guess-partner-interaction">
            <p className="prompt-text">
              Review the auction and your hand. What does partner hold?
            </p>
            <div className="reveal-button-container">
              <PrimaryButton onClick={handleBeginEstimate}>
                Make Estimate
              </PrimaryButton>
            </div>
          </div>
        );

      case FLOW_STATES.ESTIMATE:
        return (
          <div className="guess-partner-interaction">
            <div className="estimation-panel">
              {/* HCP Range Slider */}
              <div className="panel-section">
                <RangeSlider
                  label="HCP Range"
                  min={0}
                  max={37}
                  lowValue={estimates.hcpRange.low}
                  highValue={estimates.hcpRange.high}
                  onChange={handleHCPChange}
                />
              </div>

              {/* Longest Suit Selection */}
              <div className="panel-section">
                <span className="panel-label">Longest Suit</span>
                <div className="suit-choice-group">
                  {['S', 'H', 'D', 'C'].map(suit => (
                    <SuitChoiceButton
                      key={suit}
                      suit={suit}
                      selected={estimates.longestSuit === suit}
                      onClick={handleSuitSelect}
                    />
                  ))}
                </div>
              </div>

              {/* Suit Length Selection */}
              <div className="panel-section">
                <span className="panel-label">Longest Suit Length</span>
                <div className="length-choice-group">
                  {[
                    { length: 4, label: '4' },
                    { length: 5, label: '5' },
                    { length: 6, label: '6' },
                    { length: 7, label: '7+' },
                  ].map(({ length, label }) => (
                    <LengthChoiceButton
                      key={length}
                      length={length}
                      label={label}
                      selected={estimates.suitLength === length}
                      onClick={handleLengthSelect}
                    />
                  ))}
                </div>
              </div>

              {/* Shape Selection */}
              <div className="panel-section">
                <span className="panel-label">Hand Shape</span>
                <div className="shape-choice-group">
                  {[
                    { shape: SHAPE_TYPES.BALANCED, label: 'Balanced' },
                    { shape: SHAPE_TYPES.SEMI_BALANCED, label: 'Semi-balanced' },
                    { shape: SHAPE_TYPES.DISTRIBUTIONAL, label: 'Distributional' },
                  ].map(({ shape, label }) => (
                    <ShapeChoiceButton
                      key={shape}
                      shape={shape}
                      label={label}
                      selected={estimates.shape === shape}
                      onClick={handleShapeSelect}
                    />
                  ))}
                </div>
              </div>

              {/* Reveal Button */}
              <div className="reveal-button-container">
                <PrimaryButton
                  onClick={handleReveal}
                  disabled={!canReveal}
                >
                  Reveal Partner's Hand
                </PrimaryButton>
              </div>

              {!canReveal && (
                <p className="validation-message">
                  Please select all options before revealing.
                </p>
              )}
            </div>
          </div>
        );

      case FLOW_STATES.REVEAL:
        return (
          <div className="guess-partner-interaction">
            {/* Per-dimension score breakdown */}
            <div className="score-breakdown">
              {results.decisions.map((decision) => (
                <ScoreRow
                  key={decision.decisionId}
                  label={getDecisionLabel(decision.decisionId)}
                  value={decision.isCorrect ? 'Correct' : 'Incorrect'}
                  status={decision.isCorrect ? 'good' : 'bad'}
                />
              ))}
            </div>

            {/* Result explanations */}
            {results.decisions.map((decision) => (
              <ResultStrip
                key={decision.decisionId}
                type={decision.isCorrect ? 'success' : 'error'}
                message={decision.explanation}
              />
            ))}

            <div className="reveal-button-container">
              <PrimaryButton onClick={handleShowScore}>
                See Score
              </PrimaryButton>
            </div>
          </div>
        );

      case FLOW_STATES.SCORE:
        return (
          <div className="guess-partner-interaction">
            {/* Overall result */}
            <ResultStrip
              type={results.correctCount >= 3 ? 'success' : results.correctCount >= 2 ? 'info' : 'error'}
              message={`You got ${results.correctCount} of 4 correct!`}
            />

            {/* Score display */}
            <div className="overall-score">
              <span className="overall-score-label">Score</span>
              <span className={`overall-score-value ${getScoreRating(results.overallScore)}`}>
                {Math.round(results.overallScore)}%
              </span>
            </div>

            {/* Score breakdown recap */}
            <div className="score-breakdown">
              {results.decisions.map((decision) => (
                <ScoreRow
                  key={decision.decisionId}
                  label={getDecisionLabel(decision.decisionId)}
                  value={decision.isCorrect ? 'Correct' : 'Incorrect'}
                  status={decision.isCorrect ? 'good' : 'bad'}
                />
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // Render action bar content
  const renderActionContent = () => {
    if (flowState === FLOW_STATES.SCORE) {
      return (
        <div className="action-buttons">
          <SecondaryButton onClick={onClose}>
            Back to Dashboard
          </SecondaryButton>
          <PrimaryButton onClick={handleNextHand}>
            Next Hand
          </PrimaryButton>
        </div>
      );
    }
    return null;
  };

  return (
    <FlowLayout
      title="Guess Partner's Hand"
      stepIndicator={getStepIndicator()}
      onClose={onClose}
      feltContent={renderFeltContent()}
      interactionContent={renderInteractionContent()}
      actionContent={renderActionContent()}
    />
  );
}

/**
 * Get human-readable label for a decision ID
 */
function getDecisionLabel(decisionId) {
  const labels = {
    hcp: 'HCP Range',
    longestSuit: 'Longest Suit',
    suitLength: 'Suit Length',
    shape: 'Hand Shape',
  };
  return labels[decisionId] || decisionId;
}

GuessPartner.propTypes = {
  /** Callback when flow is completed with FlowResult */
  onComplete: PropTypes.func,
  /** Callback when user closes the flow */
  onClose: PropTypes.func,
  /** Optional initial scenario (for testing) */
  initialScenario: PropTypes.object,
};

export default GuessPartner;
