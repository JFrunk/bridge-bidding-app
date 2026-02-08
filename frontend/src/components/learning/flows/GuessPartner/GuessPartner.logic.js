/**
 * GuessPartner.logic.js
 *
 * Estimation scoring logic for the Guess Partner's Hand flow.
 * Evaluates player's estimates against partner's actual hand.
 *
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

import { SUIT_ORDER, groupBySuit } from '../../types/hand-types';

/**
 * Flow states for Guess Partner's Hand
 * @enum {string}
 */
export const FLOW_STATES = {
  PRESENT: 'PRESENT',
  ESTIMATE: 'ESTIMATE',
  REVEAL: 'REVEAL',
  SCORE: 'SCORE',
};

/**
 * Shape classifications for bridge hands
 * @enum {string}
 */
export const SHAPE_TYPES = {
  BALANCED: 'balanced',
  SEMI_BALANCED: 'semi-balanced',
  DISTRIBUTIONAL: 'distributional',
};

/**
 * Calculate high card points for a hand
 * @param {Array<{rank: string, suit: string}>} cards - Hand cards
 * @returns {number} HCP value (0-37)
 */
export const calculateHCP = (cards) => {
  const hcpValues = {
    'A': 4,
    'K': 3,
    'Q': 2,
    'J': 1,
  };

  return cards.reduce((total, card) => {
    return total + (hcpValues[card.rank] || 0);
  }, 0);
};

/**
 * Get suit lengths for a hand
 * @param {Array<{rank: string, suit: string}>} cards - Hand cards
 * @returns {Object.<string, number>} Suit lengths by suit letter
 */
export const getSuitLengths = (cards) => {
  const groups = groupBySuit(cards);
  return {
    S: groups.S.length,
    H: groups.H.length,
    D: groups.D.length,
    C: groups.C.length,
  };
};

/**
 * Find the longest suit(s) in a hand
 * @param {Array<{rank: string, suit: string}>} cards - Hand cards
 * @returns {{suits: string[], length: number}} Longest suit(s) and their length
 */
export const findLongestSuits = (cards) => {
  const lengths = getSuitLengths(cards);
  let maxLength = 0;

  for (const suit of SUIT_ORDER) {
    if (lengths[suit] > maxLength) {
      maxLength = lengths[suit];
    }
  }

  const suits = SUIT_ORDER.filter(suit => lengths[suit] === maxLength);

  return { suits, length: maxLength };
};

/**
 * Determine the shape classification of a hand
 * @param {Array<{rank: string, suit: string}>} cards - Hand cards
 * @returns {string} Shape type (balanced, semi-balanced, or distributional)
 */
export const determineShape = (cards) => {
  const lengths = getSuitLengths(cards);
  const sorted = Object.values(lengths).sort((a, b) => b - a);

  // Pattern representation: [longest, second, third, shortest]
  const pattern = sorted.join('-');

  // Balanced: 4-3-3-3 or 4-4-3-2
  if (pattern === '4-3-3-3' || pattern === '4-4-3-2') {
    return SHAPE_TYPES.BALANCED;
  }

  // Semi-balanced: 5-3-3-2 or 5-4-2-2
  if (pattern === '5-3-3-2' || pattern === '5-4-2-2') {
    return SHAPE_TYPES.SEMI_BALANCED;
  }

  // Distributional: 6+ card suit or void
  // Any other pattern counts as distributional
  return SHAPE_TYPES.DISTRIBUTIONAL;
};

/**
 * Score the HCP estimate
 * Correct if actual HCP is within player's range (with +/-1 tolerance at edges)
 *
 * @param {{low: number, high: number}} estimate - Player's HCP range estimate
 * @param {number} actual - Partner's actual HCP
 * @returns {{correct: boolean, explanation: string}}
 */
export const scoreHCPEstimate = (estimate, actual) => {
  const { low, high } = estimate;

  // Tolerance: +/-1 at the edges
  const effectiveLow = low - 1;
  const effectiveHigh = high + 1;

  const correct = actual >= effectiveLow && actual <= effectiveHigh;

  let explanation;
  if (correct) {
    if (actual >= low && actual <= high) {
      explanation = `Partner has ${actual} HCP, exactly within your range of ${low}-${high}.`;
    } else {
      explanation = `Partner has ${actual} HCP, just outside your ${low}-${high} range but within tolerance.`;
    }
  } else {
    explanation = `Partner has ${actual} HCP, outside your estimate of ${low}-${high}.`;
  }

  return { correct, explanation };
};

/**
 * Score the longest suit estimate
 * Correct if player's guess matches one of the tied longest suits
 *
 * @param {string} estimate - Player's suit guess ('S', 'H', 'D', 'C')
 * @param {Array<{rank: string, suit: string}>} partnerCards - Partner's cards
 * @returns {{correct: boolean, explanation: string, actualSuits: string[], actualLength: number}}
 */
export const scoreLongestSuitEstimate = (estimate, partnerCards) => {
  const { suits, length } = findLongestSuits(partnerCards);

  const correct = suits.includes(estimate);

  const suitSymbols = { S: 'spades', H: 'hearts', D: 'diamonds', C: 'clubs' };
  const estimateName = suitSymbols[estimate];

  let explanation;
  if (correct) {
    if (suits.length === 1) {
      explanation = `Correct! Partner's longest suit is ${estimateName} (${length} cards).`;
    } else {
      const suitNames = suits.map(s => suitSymbols[s]).join(' and ');
      explanation = `Correct! Partner has ${length} cards in both ${suitNames}.`;
    }
  } else {
    const suitNames = suits.map(s => suitSymbols[s]).join(' and ');
    explanation = `Partner's longest suit is ${suitNames} (${length} cards), not ${estimateName}.`;
  }

  return { correct, explanation, actualSuits: suits, actualLength: length };
};

/**
 * Score the suit length estimate
 * Correct if within +/-1 of actual length
 *
 * @param {number} estimate - Player's length guess (4, 5, 6, or 7+)
 * @param {number} actual - Actual longest suit length
 * @returns {{correct: boolean, explanation: string}}
 */
export const scoreSuitLengthEstimate = (estimate, actual) => {
  // Handle 7+ case: if player guessed 7+, actual must be 7 or more
  const effectiveEstimate = estimate;
  const effectiveActual = actual >= 7 ? 7 : actual;

  // Correct if within +/-1
  const diff = Math.abs(effectiveEstimate - effectiveActual);
  const correct = diff <= 1;

  let explanation;
  if (correct) {
    if (diff === 0) {
      explanation = `Correct! Partner's longest suit is exactly ${actual} cards.`;
    } else {
      explanation = `Close enough! Partner has ${actual} cards (you guessed ${estimate === 7 ? '7+' : estimate}).`;
    }
  } else {
    explanation = `Partner's longest suit is ${actual} cards, not ${estimate === 7 ? '7+' : estimate}.`;
  }

  return { correct, explanation };
};

/**
 * Score the shape estimate
 *
 * @param {string} estimate - Player's shape guess
 * @param {Array<{rank: string, suit: string}>} partnerCards - Partner's cards
 * @returns {{correct: boolean, explanation: string, actualShape: string}}
 */
export const scoreShapeEstimate = (estimate, partnerCards) => {
  const actualShape = determineShape(partnerCards);
  const correct = estimate === actualShape;

  const lengths = getSuitLengths(partnerCards);
  const sorted = Object.values(lengths).sort((a, b) => b - a);
  const pattern = sorted.join('-');

  const shapeLabels = {
    [SHAPE_TYPES.BALANCED]: 'balanced',
    [SHAPE_TYPES.SEMI_BALANCED]: 'semi-balanced',
    [SHAPE_TYPES.DISTRIBUTIONAL]: 'distributional',
  };

  let explanation;
  if (correct) {
    explanation = `Correct! Partner's ${pattern} shape is ${shapeLabels[actualShape]}.`;
  } else {
    explanation = `Partner's ${pattern} shape is ${shapeLabels[actualShape]}, not ${shapeLabels[estimate]}.`;
  }

  return { correct, explanation, actualShape };
};

/**
 * Score all estimates and produce decisions array
 *
 * @param {Object} estimates - Player's estimates
 * @param {Object} estimates.hcpRange - {low: number, high: number}
 * @param {string} estimates.longestSuit - 'S', 'H', 'D', or 'C'
 * @param {number} estimates.suitLength - 4, 5, 6, or 7
 * @param {string} estimates.shape - 'balanced', 'semi-balanced', or 'distributional'
 * @param {Array<{rank: string, suit: string}>} partnerCards - Partner's actual cards
 * @returns {{decisions: Array, overallScore: number, correctCount: number}}
 */
export const scoreAllEstimates = (estimates, partnerCards) => {
  const actualHCP = calculateHCP(partnerCards);
  const { suits: actualLongestSuits, length: actualLongestLength } = findLongestSuits(partnerCards);

  const hcpResult = scoreHCPEstimate(estimates.hcpRange, actualHCP);
  const suitResult = scoreLongestSuitEstimate(estimates.longestSuit, partnerCards);
  const lengthResult = scoreSuitLengthEstimate(estimates.suitLength, actualLongestLength);
  const shapeResult = scoreShapeEstimate(estimates.shape, partnerCards);

  const decisions = [
    {
      decisionId: 'hcp',
      category: 'hand-evaluation',
      playerAnswer: estimates.hcpRange,
      correctAnswer: actualHCP,
      isCorrect: hcpResult.correct,
      explanation: hcpResult.explanation,
    },
    {
      decisionId: 'longestSuit',
      category: 'hand-evaluation',
      playerAnswer: estimates.longestSuit,
      correctAnswer: actualLongestSuits,
      isCorrect: suitResult.correct,
      explanation: suitResult.explanation,
    },
    {
      decisionId: 'suitLength',
      category: 'hand-evaluation',
      playerAnswer: estimates.suitLength,
      correctAnswer: actualLongestLength,
      isCorrect: lengthResult.correct,
      explanation: lengthResult.explanation,
    },
    {
      decisionId: 'shape',
      category: 'hand-evaluation',
      playerAnswer: estimates.shape,
      correctAnswer: shapeResult.actualShape,
      isCorrect: shapeResult.correct,
      explanation: shapeResult.explanation,
    },
  ];

  const correctCount = decisions.filter(d => d.isCorrect).length;
  const overallScore = (correctCount / 4) * 100;

  return { decisions, overallScore, correctCount };
};

/**
 * Get initial estimates (default values)
 * @returns {Object} Default estimate values
 */
export const getInitialEstimates = () => ({
  hcpRange: { low: 10, high: 16 },
  longestSuit: null,
  suitLength: null,
  shape: null,
});

/**
 * Check if all estimates have been made
 * @param {Object} estimates - Current estimates
 * @returns {boolean} True if all estimates are complete
 */
export const areEstimatesComplete = (estimates) => {
  return (
    estimates.hcpRange &&
    estimates.longestSuit !== null &&
    estimates.suitLength !== null &&
    estimates.shape !== null
  );
};

/**
 * Generate FlowResult for the Guess Partner's Hand flow
 *
 * @param {string} handId - Unique hand identifier
 * @param {Array} decisions - Scored decisions
 * @param {number} overallScore - Overall score 0-100
 * @param {number} timeSpent - Time spent in milliseconds
 * @returns {Object} FlowResult object
 */
export const generateFlowResult = (handId, decisions, overallScore, timeSpent) => ({
  flowType: 'guess',
  handId,
  timestamp: new Date().toISOString(),
  decisions,
  overallScore,
  timeSpent,
  conventionTags: [],
});
