/**
 * ConventionSpotlight.logic.js
 *
 * Logic for the Convention Spotlight flow including:
 * - Flow state management
 * - Answer evaluation
 * - Progress tracking
 * - FlowResult generation
 *
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

import { QUESTION_TYPES } from './conventions.data';

/**
 * Flow states for Convention Spotlight
 * @enum {string}
 */
export const FLOW_STATES = {
  LIBRARY: 'LIBRARY',           // Convention grid view
  REFERENCE: 'REFERENCE',       // Quick reference card for selected convention
  DRILL: 'DRILL',               // Practicing with drill hands
  FEEDBACK: 'FEEDBACK',         // Showing result after answer
  CONVENTION_SUMMARY: 'CONVENTION_SUMMARY', // Session summary
};

/**
 * Initial flow state
 */
export const INITIAL_STATE = {
  flowState: FLOW_STATES.LIBRARY,
  selectedConvention: null,
  currentHandIndex: 0,
  selectedAnswer: null,
  showResult: false,
  decisions: [],
  startTime: null,
  conventionStartTime: null,
};

/**
 * Evaluate a yes/no answer
 * @param {string} playerAnswer - 'yes' or 'no'
 * @param {string} correctAnswer - 'yes' or 'no'
 * @returns {boolean} Whether the answer is correct
 */
export const evaluateYesNo = (playerAnswer, correctAnswer) => {
  return playerAnswer.toLowerCase() === correctAnswer.toLowerCase();
};

/**
 * Evaluate a bid choice answer
 * @param {string} playerAnswer - The selected choice ID
 * @param {string} correctAnswer - The correct choice ID
 * @returns {boolean} Whether the answer is correct
 */
export const evaluateBidChoice = (playerAnswer, correctAnswer) => {
  return playerAnswer === correctAnswer;
};

/**
 * Evaluate an answer based on question type
 * @param {Object} drillHand - The drill hand data
 * @param {string} playerAnswer - The player's answer
 * @returns {boolean} Whether the answer is correct
 */
export const evaluateAnswer = (drillHand, playerAnswer) => {
  const { questionType, correctAnswer } = drillHand;

  switch (questionType) {
    case QUESTION_TYPES.YES_NO:
      return evaluateYesNo(playerAnswer, correctAnswer);
    case QUESTION_TYPES.BID_CHOICE:
    case QUESTION_TYPES.FOLLOW_UP:
      return evaluateBidChoice(playerAnswer, correctAnswer);
    default:
      return false;
  }
};

/**
 * Create a decision record for tracking
 * @param {Object} drillHand - The drill hand data
 * @param {string} conventionId - The convention being tested
 * @param {number} handIndex - Index of the drill hand
 * @param {string} playerAnswer - The player's answer
 * @param {boolean} isCorrect - Whether the answer was correct
 * @returns {Object} Decision record
 */
export const createDecision = (drillHand, conventionId, handIndex, playerAnswer, isCorrect) => {
  return {
    decisionId: `${conventionId}-${handIndex}`,
    category: 'convention-recognition',
    playerAnswer,
    correctAnswer: drillHand.correctAnswer,
    isCorrect,
    explanation: drillHand.explanation,
    conventionTag: conventionId,
  };
};

/**
 * Calculate overall score from decisions
 * @param {Array} decisions - Array of decision objects
 * @returns {number} Score from 0-100
 */
export const calculateOverallScore = (decisions) => {
  if (decisions.length === 0) return 0;
  const correctCount = decisions.filter(d => d.isCorrect).length;
  return Math.round((correctCount / decisions.length) * 100);
};

/**
 * Generate FlowResult for the Convention Spotlight flow
 * @param {string} conventionId - Convention that was practiced
 * @param {Array} decisions - Scored decisions
 * @param {number} timeSpent - Time spent in milliseconds
 * @returns {Object} FlowResult object
 */
export const generateFlowResult = (conventionId, decisions, timeSpent) => {
  const overallScore = calculateOverallScore(decisions);

  return {
    flowType: 'convention',
    handId: `convention-${conventionId}-${Date.now()}`,
    timestamp: new Date().toISOString(),
    decisions,
    overallScore,
    timeSpent,
    conventionTags: [conventionId],
  };
};

/**
 * Get performance level for a convention based on accuracy
 * @param {number} accuracy - Accuracy percentage (0-100)
 * @returns {'mastered' | 'learning' | 'needs-practice'}
 */
export const getConventionMasteryLevel = (accuracy) => {
  if (accuracy >= 80) return 'mastered';
  if (accuracy >= 60) return 'learning';
  return 'needs-practice';
};

/**
 * Get related conventions for recommendation
 * @param {string} conventionId - Current convention ID
 * @param {Object} allConventions - All convention data
 * @returns {Array} Array of related convention IDs
 */
export const getRelatedConventions = (conventionId, allConventions) => {
  const current = allConventions.find(c => c.id === conventionId);
  if (!current) return [];

  // Return conventions in the same category, excluding current
  return allConventions
    .filter(c => c.category === current.category && c.id !== conventionId)
    .map(c => c.id);
};

/**
 * Shuffle drill hands for variety
 * @param {Array} drillHands - Array of drill hands
 * @param {number} [count] - Optional limit on number of hands
 * @returns {Array} Shuffled array of drill hands with original indices
 */
export const shuffleDrillHands = (drillHands, count) => {
  const indexed = drillHands.map((hand, index) => ({ ...hand, originalIndex: index }));
  const shuffled = [...indexed].sort(() => Math.random() - 0.5);
  return count ? shuffled.slice(0, count) : shuffled;
};

/**
 * Get summary statistics for a convention drill session
 * @param {Array} decisions - Array of decision objects
 * @returns {Object} Summary statistics
 */
export const getSessionSummary = (decisions) => {
  const total = decisions.length;
  const correct = decisions.filter(d => d.isCorrect).length;
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;

  return {
    total,
    correct,
    incorrect: total - correct,
    accuracy,
    masteryLevel: getConventionMasteryLevel(accuracy),
  };
};

/**
 * Format time spent in human-readable format
 * @param {number} ms - Milliseconds
 * @returns {string} Formatted time string
 */
export const formatTimeSpent = (ms) => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  }
  return `${minutes}m ${remainingSeconds}s`;
};

/**
 * Determine if user should continue to next hand or see summary
 * @param {number} currentIndex - Current hand index
 * @param {number} totalHands - Total number of drill hands
 * @returns {boolean} True if there are more hands
 */
export const hasMoreHands = (currentIndex, totalHands) => {
  return currentIndex < totalHands - 1;
};

/**
 * Get choices for Yes/No questions
 * @returns {Array} Choice objects for yes/no
 */
export const getYesNoChoices = () => [
  { id: 'yes', label: 'Yes' },
  { id: 'no', label: 'No' },
];

/**
 * State reducer for the flow
 * @param {Object} state - Current state
 * @param {Object} action - Action to perform
 * @returns {Object} New state
 */
export const flowReducer = (state, action) => {
  switch (action.type) {
    case 'SELECT_CONVENTION':
      return {
        ...state,
        flowState: FLOW_STATES.REFERENCE,
        selectedConvention: action.convention,
        currentHandIndex: 0,
        decisions: [],
        conventionStartTime: Date.now(),
      };

    case 'START_DRILL':
      return {
        ...state,
        flowState: FLOW_STATES.DRILL,
        currentHandIndex: 0,
        selectedAnswer: null,
        showResult: false,
      };

    case 'SELECT_ANSWER':
      return {
        ...state,
        selectedAnswer: action.answer,
      };

    case 'SUBMIT_ANSWER':
      return {
        ...state,
        flowState: FLOW_STATES.FEEDBACK,
        showResult: true,
        decisions: [...state.decisions, action.decision],
      };

    case 'NEXT_HAND':
      return {
        ...state,
        flowState: FLOW_STATES.DRILL,
        currentHandIndex: state.currentHandIndex + 1,
        selectedAnswer: null,
        showResult: false,
      };

    case 'SHOW_SUMMARY':
      return {
        ...state,
        flowState: FLOW_STATES.CONVENTION_SUMMARY,
      };

    case 'BACK_TO_LIBRARY':
      return {
        ...INITIAL_STATE,
        startTime: state.startTime,
      };

    case 'BACK_TO_REFERENCE':
      return {
        ...state,
        flowState: FLOW_STATES.REFERENCE,
        currentHandIndex: 0,
        selectedAnswer: null,
        showResult: false,
        decisions: [],
      };

    case 'RESET':
      return {
        ...INITIAL_STATE,
        startTime: Date.now(),
      };

    default:
      return state;
  }
};

export default {
  FLOW_STATES,
  INITIAL_STATE,
  evaluateAnswer,
  createDecision,
  calculateOverallScore,
  generateFlowResult,
  getConventionMasteryLevel,
  getRelatedConventions,
  shuffleDrillHands,
  getSessionSummary,
  formatTimeSpent,
  hasMoreHands,
  getYesNoChoices,
  flowReducer,
};
