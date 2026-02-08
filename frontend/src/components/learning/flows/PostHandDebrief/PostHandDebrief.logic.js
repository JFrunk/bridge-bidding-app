/**
 * PostHandDebrief.logic.js
 *
 * Business logic for the Post-Hand Debrief flow.
 * Handles decision evaluation and timeline building.
 */

import { formatBid } from '../../types/flow-types';

/**
 * Decision status types for timeline
 * @typedef {'correct' | 'wrong' | 'neutral'} DecisionStatus
 */

/**
 * Timeline step structure
 * @typedef {Object} TimelineStep
 * @property {string} id - Unique step ID
 * @property {number} round - Round number (for ordering)
 * @property {'bid' | 'play' | 'result'} type - Type of decision
 * @property {string} label - Short label like "Round 1"
 * @property {string} detail - Description with bids/actions
 * @property {string} explanation - Why correct or what was better
 * @property {DecisionStatus} status - correct, wrong, or neutral
 * @property {string} [playerBid] - Player's bid if applicable
 * @property {string} [optimalBid] - Optimal bid if different
 */

/**
 * Format contract for display
 * @param {Object} contract - Contract object
 * @returns {string} Formatted contract like "3NT" or "4S"
 */
export const formatContract = (contract) => {
  if (!contract) return '';

  const strainMap = {
    'S': 'S',
    'H': 'H',
    'D': 'D',
    'C': 'C',
    'NT': 'NT'
  };

  const strain = strainMap[contract.strain] || contract.strain;
  let result = `${contract.level}${strain}`;

  if (contract.doubled) result += 'X';
  if (contract.redoubled) result += 'XX';

  return result;
};

/**
 * Format result for display in contract bar
 * @param {Object} result - Result object with tricksRequired, tricksMade
 * @returns {string} Formatted result like "Made +1" or "Down 2"
 */
export const formatResult = (result) => {
  if (!result) return '';

  const diff = result.tricksMade - result.tricksRequired;

  if (diff === 0) {
    return 'Made exactly';
  } else if (diff > 0) {
    return `Made +${diff}`;
  } else {
    return `Down ${Math.abs(diff)}`;
  }
};

/**
 * Get the declarer display name
 * @param {string} declarerPosition - 'N', 'E', 'S', 'W'
 * @returns {string} Display name like "North" or "South"
 */
export const getDeclarerName = (declarerPosition) => {
  const names = {
    'N': 'North',
    'E': 'East',
    'S': 'South',
    'W': 'West'
  };
  return names[declarerPosition] || declarerPosition;
};

/**
 * Map decision status to timeline status
 * @param {boolean} isCorrect - Whether the decision was correct
 * @param {string} type - Decision type ('bid', 'play', 'result')
 * @returns {DecisionStatus}
 */
const getDecisionStatus = (isCorrect, type) => {
  // Result type decisions that are correct are neutral (just info)
  if (type === 'result' && isCorrect) {
    return 'neutral';
  }
  return isCorrect ? 'correct' : 'wrong';
};

/**
 * Build timeline step from a decision
 * @param {Object} decision - Decision object from hand data
 * @returns {TimelineStep}
 */
const buildTimelineStep = (decision) => {
  const { decisionId, round, type, playerAction, optimalAction, isCorrect, explanation } = decision;

  const status = getDecisionStatus(isCorrect, type);

  // Build label based on type and round
  let label;
  if (type === 'result') {
    label = 'Result';
  } else if (type === 'play') {
    label = `Play ${round - 2}`; // Adjust for bidding rounds
  } else {
    label = `Round ${round}`;
  }

  // Build detail text
  let detail;
  if (type === 'bid') {
    if (isCorrect) {
      detail = `Your bid: ${formatBid(playerAction)}`;
    } else {
      detail = `Your bid: ${formatBid(playerAction)} — Better: ${formatBid(optimalAction)}`;
    }
  } else {
    detail = playerAction;
  }

  return {
    id: decisionId,
    round,
    type,
    label,
    detail,
    explanation,
    status,
    playerBid: type === 'bid' ? playerAction : null,
    optimalBid: type === 'bid' && !isCorrect ? optimalAction : null
  };
};

/**
 * Build the complete timeline from hand decisions
 * @param {Object[]} decisions - Array of decision objects
 * @returns {TimelineStep[]} Ordered timeline steps
 */
export const buildTimeline = (decisions) => {
  if (!decisions || !Array.isArray(decisions)) {
    return [];
  }

  return decisions
    .map(buildTimelineStep)
    .sort((a, b) => a.round - b.round);
};

/**
 * Calculate overall score from timeline
 * @param {TimelineStep[]} timeline - Built timeline steps
 * @returns {number} Score 0-100
 */
export const calculateScore = (timeline) => {
  if (!timeline || timeline.length === 0) {
    return 0;
  }

  // Filter to only scoreable decisions (not neutral)
  const scoreableSteps = timeline.filter(step => step.status !== 'neutral');

  if (scoreableSteps.length === 0) {
    return 100; // All neutral means perfect
  }

  const correctSteps = scoreableSteps.filter(step => step.status === 'correct');
  return Math.round((correctSteps.length / scoreableSteps.length) * 100);
};

/**
 * Count decisions by status
 * @param {TimelineStep[]} timeline - Built timeline steps
 * @returns {{ correct: number, wrong: number, neutral: number }}
 */
export const countDecisions = (timeline) => {
  return {
    correct: timeline.filter(s => s.status === 'correct').length,
    wrong: timeline.filter(s => s.status === 'wrong').length,
    neutral: timeline.filter(s => s.status === 'neutral').length
  };
};

/**
 * Build the FlowResult object for this debrief
 * @param {Object} handData - Complete hand data
 * @param {TimelineStep[]} timeline - Built timeline
 * @param {number} startTime - When the flow started (Date.now())
 * @returns {Object} FlowResult object
 */
export const buildFlowResult = (handData, timeline, startTime) => {
  const scoreableDecisions = timeline.filter(s => s.status !== 'neutral');

  return {
    flowType: 'debrief',
    handId: handData.handId,
    timestamp: new Date().toISOString(),
    decisions: scoreableDecisions.map(step => ({
      decisionId: step.id,
      category: step.type,
      playerAnswer: step.playerBid || step.detail,
      correctAnswer: step.optimalBid || step.detail,
      isCorrect: step.status === 'correct',
      explanation: step.explanation
    })),
    overallScore: calculateScore(timeline),
    timeSpent: Date.now() - startTime,
    conventionTags: [] // Could be extracted from decisions if needed
  };
};

/**
 * Determine if this was a successful hand overall
 * @param {Object} result - Hand result object
 * @returns {boolean}
 */
export const wasHandSuccessful = (result) => {
  if (!result) return false;
  return result.tricksMade >= result.tricksRequired;
};

/**
 * Get the score status for styling
 * @param {number} score - Score 0-100
 * @returns {'good' | 'medium' | 'weak'}
 */
export const getScoreStatus = (score) => {
  if (score >= 80) return 'good';
  if (score >= 60) return 'medium';
  return 'weak';
};
