/**
 * CriticalTrick.jsx
 * Play the Critical Trick Flow (Flow 8)
 *
 * A declarer play training flow where users choose the best plan
 * for critical situations (finesse vs drop, hold-up, endplay, etc.)
 *
 * Flow States: PRESENT -> CHOOSE_PLAN -> RESULT
 */

import React, { useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import { FlowLayout, HandDisplay, ResultStrip, PrimaryButton } from '../../shared';
import TrickBar from './TrickBar';
import {
  evaluatePlan,
  parseContract,
  generateFlowResult,
  getTechniqueDescription
} from './CriticalTrick.logic';
import { getRandomProblem } from './mockData';
import './CriticalTrick.css';

// Flow states
const STATES = {
  PRESENT: 'PRESENT',
  CHOOSE_PLAN: 'CHOOSE_PLAN',
  RESULT: 'RESULT'
};

/**
 * Colorize suit symbols in text
 * @param {string} text - Text containing suit symbols
 * @returns {React.ReactNode[]} JSX with colored spans
 */
function colorizeSuits(text) {
  if (!text) return text;

  const parts = [];
  let lastIndex = 0;
  const suitPattern = /([♠♣♥♦])/g;
  let match;

  while ((match = suitPattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const symbol = match[1];
    const isRed = symbol === '♥' || symbol === '♦';
    parts.push(
      <span key={match.index} className={isRed ? 'suit-red' : 'suit-black'}>
        {symbol}
      </span>
    );

    lastIndex = match.index + 1;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

/**
 * @param {Object} props
 * @param {Object} props.problem - Optional problem to use (uses random if not provided)
 * @param {Function} props.onComplete - Called with FlowResult when flow completes
 * @param {Function} props.onClose - Called when user closes the flow
 */
function CriticalTrick({ problem: initialProblem = null, onComplete = null, onClose = null }) {
  // Use provided problem or get a random one
  const [problem] = useState(() => initialProblem || getRandomProblem());

  // Flow state
  const [flowState, setFlowState] = useState(STATES.PRESENT);
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [startTime] = useState(() => Date.now());

  // Parse contract for display
  const contractInfo = useMemo(() => parseContract(problem.contract), [problem.contract]);

  // Get current trick number
  const currentTrick = problem.tricksSoFar.ns + problem.tricksSoFar.ew + 1;

  // Handle plan selection
  const handlePlanSelect = useCallback((planId) => {
    if (flowState !== STATES.PRESENT) return;

    setSelectedPlanId(planId);
    setFlowState(STATES.CHOOSE_PLAN);

    // Simulate brief evaluation delay
    setTimeout(() => {
      const result = evaluatePlan(planId, problem);
      setEvaluation(result);
      setFlowState(STATES.RESULT);
    }, 600);
  }, [flowState, problem]);

  // Handle next/complete
  const handleNext = useCallback(() => {
    if (!evaluation) return;

    const timeSpent = Date.now() - startTime;
    const flowResult = generateFlowResult(problem, evaluation, timeSpent);

    if (onComplete) {
      onComplete(flowResult);
    }
  }, [evaluation, problem, startTime, onComplete]);

  // Get plan button classes
  const getPlanClasses = (planId) => {
    const classes = ['plan-choice'];

    if (flowState === STATES.CHOOSE_PLAN && planId !== selectedPlanId) {
      classes.push('disabled');
    }

    if (flowState === STATES.RESULT) {
      const plan = problem.plans.find(p => p.id === planId);
      if (plan?.isCorrect) {
        classes.push('correct');
      } else if (planId === selectedPlanId && !plan?.isCorrect) {
        classes.push('wrong');
      } else {
        classes.push('disabled');
      }
    } else if (planId === selectedPlanId) {
      classes.push('selected');
    }

    return classes.join(' ');
  };

  // Vulnerability display
  const getVulnerabilityClass = () => {
    const vul = problem.vulnerability;
    if (vul === 'NS' || vul === 'Both') return 'vulnerability-badge vul-ns';
    return 'vulnerability-badge';
  };

  const getVulnerabilityText = () => {
    switch (problem.vulnerability) {
      case 'NS': return 'Vul';
      case 'EW': return 'Opp Vul';
      case 'Both': return 'Both Vul';
      default: return 'Non-Vul';
    }
  };

  // Felt zone content
  const feltContent = (
    <>
      {/* Contract display */}
      <div className="critical-contract">
        <div className="contract-badge">
          {colorizeSuits(contractInfo.displayContract)}
        </div>
        <span className={getVulnerabilityClass()}>
          {getVulnerabilityText()}
        </span>
      </div>

      {/* Trick bar */}
      <TrickBar
        tricksWonNS={problem.tricksSoFar.ns}
        tricksWonEW={problem.tricksSoFar.ew}
        tricksNeeded={contractInfo.tricksNeeded}
        currentTrick={currentTrick}
      />

      {/* Hands display */}
      <div className="critical-hands">
        <div className="hand-section">
          <div className="hand-label">Dummy</div>
          <HandDisplay cards={problem.dummyHand} mode="hand-h" />
        </div>
        <div className="hand-section">
          <div className="hand-label">Your Hand</div>
          <HandDisplay cards={problem.declarerHand} mode="hand-h" />
        </div>
      </div>

      {/* Situation description */}
      <div className="situation-box">
        <p className="situation-text">
          {colorizeSuits(problem.situationText)}
        </p>
      </div>
    </>
  );

  // Interaction zone content
  const interactionContent = (
    <>
      {flowState === STATES.PRESENT && (
        <>
          <h3 className="question-header">What's your plan?</h3>
          <div className="plan-grid">
            {problem.plans.map((plan) => (
              <button
                key={plan.id}
                className={getPlanClasses(plan.id)}
                onClick={() => handlePlanSelect(plan.id)}
                type="button"
              >
                {colorizeSuits(plan.label)}
              </button>
            ))}
          </div>
        </>
      )}

      {flowState === STATES.CHOOSE_PLAN && (
        <>
          <h3 className="question-header">What's your plan?</h3>
          <div className="plan-grid">
            {problem.plans.map((plan) => (
              <button
                key={plan.id}
                className={getPlanClasses(plan.id)}
                disabled
                type="button"
              >
                {colorizeSuits(plan.label)}
              </button>
            ))}
          </div>
          <div className="evaluating-indicator">
            <div className="evaluating-spinner" />
            <span>Evaluating...</span>
          </div>
        </>
      )}

      {flowState === STATES.RESULT && evaluation && (
        <>
          <ResultStrip
            type={evaluation.isCorrect ? 'success' : 'error'}
            message={evaluation.isCorrect ? 'Correct!' : 'Not quite right'}
            detail={evaluation.isCorrect ? evaluation.technique : `The correct plan: ${evaluation.correctPlan?.technique}`}
          />

          <div className="plan-grid">
            {problem.plans.map((plan) => (
              <button
                key={plan.id}
                className={getPlanClasses(plan.id)}
                disabled
                type="button"
              >
                {colorizeSuits(plan.label)}
              </button>
            ))}
          </div>

          <div className="explanation-box">
            <div className="explanation-label">Explanation</div>
            <p className="explanation-text">{evaluation.explanation}</p>
            <span className="technique-badge">{problem.technique}</span>
          </div>
        </>
      )}
    </>
  );

  // Action bar content
  const actionContent = flowState === STATES.RESULT ? (
    <PrimaryButton onClick={handleNext}>
      Continue
    </PrimaryButton>
  ) : null;

  return (
    <FlowLayout
      title="Critical Trick"
      stepIndicator={`Technique: ${problem.technique}`}
      onClose={onClose}
      feltContent={feltContent}
      interactionContent={interactionContent}
      actionContent={actionContent}
    />
  );
}

CriticalTrick.propTypes = {
  problem: PropTypes.shape({
    id: PropTypes.string.isRequired,
    contract: PropTypes.string.isRequired,
    vulnerability: PropTypes.string.isRequired,
    dummyHand: PropTypes.arrayOf(
      PropTypes.shape({
        rank: PropTypes.string.isRequired,
        suit: PropTypes.string.isRequired,
      })
    ).isRequired,
    declarerHand: PropTypes.arrayOf(
      PropTypes.shape({
        rank: PropTypes.string.isRequired,
        suit: PropTypes.string.isRequired,
      })
    ).isRequired,
    tricksSoFar: PropTypes.shape({
      ns: PropTypes.number.isRequired,
      ew: PropTypes.number.isRequired,
    }).isRequired,
    tricksNeeded: PropTypes.number,
    situationText: PropTypes.string.isRequired,
    plans: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired,
        isCorrect: PropTypes.bool.isRequired,
        explanation: PropTypes.string.isRequired,
        technique: PropTypes.string.isRequired,
      })
    ).isRequired,
    technique: PropTypes.string.isRequired,
  }),
  onComplete: PropTypes.func,
  onClose: PropTypes.func,
};

export default CriticalTrick;
