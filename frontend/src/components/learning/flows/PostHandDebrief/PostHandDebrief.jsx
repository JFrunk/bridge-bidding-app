/**
 * PostHandDebrief.jsx
 *
 * Post-Hand Debrief flow (Flow 4) for the learning system.
 * A review screen (NOT a quiz) showing all four hands, decision timeline,
 * and result summary.
 *
 * Layout:
 * - Header with board number
 * - Contract bar with result
 * - Two-column content: four hands grid + decision timeline
 * - Action buttons: Replay Hand / Next Hand
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  FlowLayout,
  HandDiagram,
  PrimaryButton,
  SecondaryButton
} from '../../shared';
import DecisionTimeline from './DecisionTimeline';
import {
  buildTimeline,
  calculateScore,
  countDecisions,
  buildFlowResult,
  formatContract,
  formatResult,
  getDeclarerName,
  wasHandSuccessful,
  getScoreStatus
} from './PostHandDebrief.logic';
import { formatBid } from '../../types/flow-types';
import { SUIT_SYMBOLS } from '../../types/hand-types';
import './PostHandDebrief.css';

/**
 * ContractBar - Displays the contract and result
 */
const ContractBar = ({ contract, result }) => {
  const contractDisplay = formatContract(contract);
  const resultDisplay = formatResult(result);
  const isSuccess = wasHandSuccessful(result);
  const declarerName = getDeclarerName(contract?.declarer);

  // Format contract with suit symbol
  const formatContractDisplay = (contractStr) => {
    if (!contractStr) return '';

    // Map strain letters to symbols
    const strainMap = {
      'S': SUIT_SYMBOLS.S,
      'H': SUIT_SYMBOLS.H,
      'D': SUIT_SYMBOLS.D,
      'C': SUIT_SYMBOLS.C
    };

    let result = contractStr;
    // Replace strain letter with symbol (but not NT)
    for (const [letter, symbol] of Object.entries(strainMap)) {
      result = result.replace(new RegExp(`(\\d)${letter}(?!T)`, 'g'), `$1${symbol}`);
    }
    return result;
  };

  return (
    <div className="contract-bar">
      <span className="contract-bar-contract">
        {formatContractDisplay(contractDisplay)}
      </span>
      <span className="contract-bar-by">
        by {declarerName}
      </span>
      <span className={`contract-bar-result ${isSuccess ? 'success' : 'failure'}`}>
        {resultDisplay}
      </span>
    </div>
  );
};

ContractBar.propTypes = {
  contract: PropTypes.shape({
    level: PropTypes.number.isRequired,
    strain: PropTypes.string.isRequired,
    declarer: PropTypes.string.isRequired,
    doubled: PropTypes.bool,
    redoubled: PropTypes.bool
  }).isRequired,
  result: PropTypes.shape({
    tricksRequired: PropTypes.number.isRequired,
    tricksMade: PropTypes.number.isRequired,
    overtricks: PropTypes.number,
    score: PropTypes.number
  }).isRequired
};

/**
 * FourHandsDisplay - 2x2 grid of all four hands
 */
const FourHandsDisplay = ({ allHands, playerPosition = 'S' }) => {
  // Position order: North (top-left), East (top-right), West (bottom-left), South (bottom-right)
  const positions = [
    { key: 'north', label: 'North', position: 'N' },
    { key: 'east', label: 'East', position: 'E' },
    { key: 'west', label: 'West', position: 'W' },
    { key: 'south', label: 'South', position: 'S' }
  ];

  return (
    <div className="four-hands-panel">
      <div className="four-hands-title">All Four Hands</div>
      <div className="four-hands-grid">
        {positions.map(({ key, label, position }) => (
          <div key={key} className="hand-cell">
            <span className={`hand-cell-label ${position === playerPosition ? 'player' : ''}`}>
              {label}
              {position === playerPosition && ' (You)'}
            </span>
            <HandDiagram
              cards={allHands[key] || []}
              highlight={position === playerPosition}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

FourHandsDisplay.propTypes = {
  allHands: PropTypes.shape({
    north: PropTypes.array.isRequired,
    east: PropTypes.array.isRequired,
    south: PropTypes.array.isRequired,
    west: PropTypes.array.isRequired
  }).isRequired,
  playerPosition: PropTypes.oneOf(['N', 'E', 'S', 'W'])
};


/**
 * ScoreSummary - Shows decision counts and overall score
 */
const ScoreSummary = ({ timeline, score }) => {
  const counts = countDecisions(timeline);
  const scoreStatus = getScoreStatus(score);

  return (
    <div className="score-summary">
      <div className="score-summary-item">
        <span className="score-summary-label">Correct</span>
        <span className="score-summary-value good">{counts.correct}</span>
      </div>
      <div className="score-summary-item">
        <span className="score-summary-label">Mistakes</span>
        <span className="score-summary-value weak">{counts.wrong}</span>
      </div>
      <div className="score-summary-item">
        <span className="score-summary-label">Score</span>
        <span className={`score-summary-value ${scoreStatus}`}>{score}%</span>
      </div>
    </div>
  );
};

ScoreSummary.propTypes = {
  timeline: PropTypes.array.isRequired,
  score: PropTypes.number.isRequired
};

/**
 * PostHandDebrief - Main component
 *
 * @param {Object} props
 * @param {Object} props.handData - Complete hand data with decisions
 * @param {function} props.onReplay - Handler for replay button
 * @param {function} props.onNext - Handler for next hand button
 * @param {function} props.onClose - Handler for close button
 * @param {function} props.onComplete - Called with FlowResult when done
 */
const PostHandDebrief = ({
  handData = null,
  onReplay = () => {},
  onNext = () => {},
  onClose = null,
  onComplete = null
}) => {
  const [startTime] = useState(Date.now());
  const [timeline, setTimeline] = useState([]);
  const [score, setScore] = useState(0);

  // Build timeline on mount or when handData changes
  useEffect(() => {
    if (handData?.decisions) {
      const builtTimeline = buildTimeline(handData.decisions);
      setTimeline(builtTimeline);
      setScore(calculateScore(builtTimeline));
    }
  }, [handData]);

  // Handle next hand with flow result
  const handleNext = useCallback(() => {
    if (onComplete) {
      const flowResult = buildFlowResult(handData, timeline, startTime);
      onComplete(flowResult);
    }
    if (onNext) {
      onNext();
    }
  }, [handData, timeline, startTime, onComplete, onNext]);

  // Guard against missing data
  if (!handData) {
    return (
      <FlowLayout
        title="Hand Review"
        onClose={onClose}
        interactionContent={
          <div className="debrief-container">
            <p style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No hand data available
            </p>
          </div>
        }
      />
    );
  }

  const { boardNumber, allHands, contract, result } = handData;

  return (
    <div className="debrief-flow">
      <FlowLayout
        title={`Hand Review — Board #${boardNumber || '?'}`}
        onClose={onClose}
        interactionContent={
          <div className="debrief-container">
            {/* Contract Bar */}
            {contract && result && (
              <ContractBar contract={contract} result={result} />
            )}

            {/* Main Content: Hands + Timeline */}
            <div className="debrief-content">
              {/* Four Hands Grid */}
              {allHands && (
                <FourHandsDisplay allHands={allHands} playerPosition="S" />
              )}

              {/* Decision Timeline */}
              <div className="timeline-panel">
                <div className="timeline-title">Decision Timeline</div>
                <div className="timeline-scroll">
                  <DecisionTimeline steps={timeline} />
                </div>
              </div>
            </div>

            {/* Score Summary */}
            <ScoreSummary timeline={timeline} score={score} />

            {/* Action Buttons */}
            <div className="debrief-actions">
              <SecondaryButton onClick={onReplay}>
                Replay Hand
              </SecondaryButton>
              <PrimaryButton onClick={handleNext}>
                Next Hand
              </PrimaryButton>
            </div>
          </div>
        }
      />
    </div>
  );
};

PostHandDebrief.propTypes = {
  handData: PropTypes.shape({
    handId: PropTypes.string,
    boardNumber: PropTypes.number,
    allHands: PropTypes.shape({
      north: PropTypes.array,
      east: PropTypes.array,
      south: PropTypes.array,
      west: PropTypes.array
    }),
    auction: PropTypes.array,
    contract: PropTypes.shape({
      level: PropTypes.number,
      strain: PropTypes.string,
      declarer: PropTypes.string,
      doubled: PropTypes.bool,
      redoubled: PropTypes.bool
    }),
    result: PropTypes.shape({
      tricksRequired: PropTypes.number,
      tricksMade: PropTypes.number,
      overtricks: PropTypes.number,
      score: PropTypes.number
    }),
    decisions: PropTypes.arrayOf(
      PropTypes.shape({
        decisionId: PropTypes.string,
        round: PropTypes.number,
        type: PropTypes.string,
        playerAction: PropTypes.string,
        optimalAction: PropTypes.string,
        isCorrect: PropTypes.bool,
        explanation: PropTypes.string
      })
    )
  }),
  onReplay: PropTypes.func,
  onNext: PropTypes.func,
  onClose: PropTypes.func,
  onComplete: PropTypes.func
};

export default PostHandDebrief;
