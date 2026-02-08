/**
 * OpeningLead.logic.js
 *
 * Lead evaluation logic for the Opening Lead Quiz flow.
 * Evaluates player's lead selection against DDS analysis.
 */

import { SUIT_SYMBOLS } from '../../types/hand-types';
import { generateHandId } from '../../types/flow-types';

/**
 * Flow states for the Opening Lead Quiz
 */
export const FLOW_STATES = {
  PRESENT: 'PRESENT',   // Show hand and prompt to select lead
  SELECT: 'SELECT',     // Card selected, evaluating
  EVALUATE: 'EVALUATE', // Show evaluation result
  RESULT: 'RESULT'      // Final result with explanation
};

/**
 * Compare two cards for equality
 * @param {Object} card1 - { rank, suit }
 * @param {Object} card2 - { rank, suit }
 * @returns {boolean}
 */
export const cardsEqual = (card1, card2) => {
  if (!card1 || !card2) return false;
  return card1.rank === card2.rank && card1.suit === card2.suit;
};

/**
 * Format a card for display
 * @param {Object} card - { rank, suit }
 * @returns {string} e.g., "K of Spades" or "K♠"
 */
export const formatCard = (card, verbose = false) => {
  if (!card) return '';
  const symbol = SUIT_SYMBOLS[card.suit] || card.suit;
  if (verbose) {
    const suitNames = { S: 'Spades', H: 'Hearts', D: 'Diamonds', C: 'Clubs' };
    return `${card.rank} of ${suitNames[card.suit]}`;
  }
  return `${card.rank}${symbol}`;
};

/**
 * Find the lead evaluation for a specific card
 * @param {Object} card - Selected card { rank, suit }
 * @param {Array} evaluations - Array of lead evaluations
 * @returns {Object|null} The evaluation for this card or null
 */
export const findLeadEvaluation = (card, evaluations) => {
  if (!card || !evaluations) return null;
  return evaluations.find(leadEval => cardsEqual(leadEval.card, card)) || null;
};

/**
 * Find the optimal lead from evaluations
 * @param {Array} evaluations - Array of lead evaluations
 * @returns {Object|null} The evaluation with the most defensive tricks
 */
export const findOptimalLead = (evaluations) => {
  if (!evaluations || evaluations.length === 0) return null;
  return evaluations.reduce((best, current) => {
    return current.defensiveTricks > best.defensiveTricks ? current : best;
  });
};

/**
 * Evaluate a player's lead selection
 * @param {Object} selectedCard - The card the player selected
 * @param {Object} handData - The mock hand data with evaluations
 * @returns {Object} Evaluation result with isCorrect, score, and details
 */
export const evaluateLead = (selectedCard, handData) => {
  const { leadEvaluations, optimalLead, explanation } = handData;

  // Find evaluations
  const playerEvaluation = findLeadEvaluation(selectedCard, leadEvaluations);
  const optimalEvaluation = findLeadEvaluation(optimalLead, leadEvaluations);

  // Check if the selected lead matches the optimal lead
  const isOptimal = cardsEqual(selectedCard, optimalLead);

  // Calculate score based on trick difference
  let score = 0;
  let rating = 'error';

  if (isOptimal) {
    score = 100;
    rating = 'optimal';
  } else if (playerEvaluation && optimalEvaluation) {
    const trickDifference = optimalEvaluation.defensiveTricks - playerEvaluation.defensiveTricks;

    if (trickDifference === 0) {
      // Same number of tricks - acceptable alternative
      score = 100;
      rating = 'optimal';
    } else if (trickDifference === 1) {
      // One trick worse - suboptimal but not terrible
      score = 60;
      rating = 'acceptable';
    } else if (trickDifference === 2) {
      // Two tricks worse - poor choice
      score = 30;
      rating = 'suboptimal';
    } else {
      // Three or more tricks worse - significant error
      score = 0;
      rating = 'error';
    }
  }

  return {
    isCorrect: isOptimal,
    score,
    rating,
    selectedCard,
    optimalCard: optimalLead,
    playerEvaluation: playerEvaluation || {
      card: selectedCard,
      defensiveTricks: 0,
      contractResult: 'Unknown'
    },
    optimalEvaluation: optimalEvaluation || {
      card: optimalLead,
      defensiveTricks: 0,
      contractResult: 'Unknown'
    },
    explanation,
    trickDifference: playerEvaluation && optimalEvaluation
      ? optimalEvaluation.defensiveTricks - playerEvaluation.defensiveTricks
      : 0
  };
};

/**
 * Get lead comparison data for the compare table
 * @param {Array} evaluations - All lead evaluations
 * @param {Object} selectedCard - Player's selected card
 * @param {Object} optimalCard - The optimal card
 * @returns {Array} Sorted array of leads for comparison table
 */
export const getLeadComparison = (evaluations, selectedCard, optimalCard) => {
  if (!evaluations) return [];

  // Sort by defensive tricks (descending)
  const sorted = [...evaluations].sort((a, b) => b.defensiveTricks - a.defensiveTricks);

  // Take top 5 leads (or all if fewer)
  const topLeads = sorted.slice(0, 5);

  // Make sure player's lead is included if not in top 5
  const playerInTop = topLeads.some(e => cardsEqual(e.card, selectedCard));
  if (!playerInTop && selectedCard) {
    const playerEval = evaluations.find(e => cardsEqual(e.card, selectedCard));
    if (playerEval) {
      topLeads.push(playerEval);
    }
  }

  // Map to comparison format with highlighting
  return topLeads.map(evaluation => ({
    card: evaluation.card,
    cardDisplay: formatCard(evaluation.card),
    defensiveTricks: evaluation.defensiveTricks,
    contractResult: evaluation.contractResult,
    isPlayerChoice: cardsEqual(evaluation.card, selectedCard),
    isOptimal: cardsEqual(evaluation.card, optimalCard),
    status: cardsEqual(evaluation.card, optimalCard) ? 'good' :
            cardsEqual(evaluation.card, selectedCard) ? 'neutral' : undefined
  }));
};

/**
 * Format contract for display
 * @param {Object} contract - Contract object
 * @returns {string} e.g., "4♠ by South"
 */
export const formatContract = (contract) => {
  if (!contract) return '';
  const strainMap = {
    S: '♠',
    H: '♥',
    D: '♦',
    C: '♣',
    NT: 'NT'
  };
  const declarerMap = {
    N: 'North',
    E: 'East',
    S: 'South',
    W: 'West'
  };

  const strain = strainMap[contract.strain] || contract.strain;
  const declarer = declarerMap[contract.declarer] || contract.declarer;
  let result = `${contract.level}${strain}`;

  if (contract.doubled) result += ' X';
  if (contract.redoubled) result += ' XX';

  return `${result} by ${declarer}`;
};

/**
 * Get defender position name
 * @param {'W' | 'E'} leader - Leader position
 * @returns {string} "West" or "East"
 */
export const getLeaderName = (leader) => {
  return leader === 'W' ? 'West' : 'East';
};

/**
 * Create a FlowResult object for the Opening Lead flow
 * @param {Object} handData - The mock hand data
 * @param {Object} evaluationResult - Result from evaluateLead
 * @param {number} timeSpent - Time spent in milliseconds
 * @returns {Object} FlowResult object
 */
export const createFlowResult = (handData, evaluationResult, timeSpent) => {
  const timestamp = new Date().toISOString();

  return {
    flowType: 'lead',
    handId: handData.id || generateHandId(),
    timestamp,
    decisions: [{
      decisionId: 'opening-lead',
      category: 'Opening Leads',
      playerAnswer: formatCard(evaluationResult.selectedCard),
      correctAnswer: formatCard(evaluationResult.optimalCard),
      isCorrect: evaluationResult.isCorrect,
      explanation: evaluationResult.explanation,
      conventionTag: null
    }],
    overallScore: evaluationResult.isCorrect ? 100 : 0,
    timeSpent,
    conventionTags: []
  };
};

/**
 * Get result message based on evaluation
 * @param {Object} evaluationResult - Result from evaluateLead
 * @returns {Object} { type: 'success'|'error', message: string, detail: string }
 */
export const getResultMessage = (evaluationResult) => {
  const { isCorrect, rating, trickDifference, selectedCard, optimalCard } = evaluationResult;

  if (isCorrect || rating === 'optimal') {
    return {
      type: 'success',
      message: 'Excellent lead!',
      detail: `${formatCard(selectedCard)} is the optimal choice.`
    };
  }

  if (rating === 'acceptable') {
    return {
      type: 'info',
      message: 'Close, but not optimal',
      detail: `${formatCard(optimalCard)} would gain ${trickDifference} extra trick${trickDifference > 1 ? 's' : ''}.`
    };
  }

  return {
    type: 'error',
    message: 'Not the best lead',
    detail: `${formatCard(optimalCard)} would gain ${trickDifference} trick${trickDifference > 1 ? 's' : ''} on defense.`
  };
};

export default {
  FLOW_STATES,
  evaluateLead,
  getLeadComparison,
  findOptimalLead,
  formatCard,
  formatContract,
  getLeaderName,
  createFlowResult,
  getResultMessage,
  cardsEqual
};
