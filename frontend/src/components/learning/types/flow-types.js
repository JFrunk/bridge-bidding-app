/**
 * Flow Type Definitions for Learning Flows
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 *
 * These are JSDoc type definitions for use with JavaScript components.
 */

/**
 * @typedef {'daily' | 'lead' | 'guess' | 'debrief' | 'count' | 'replay' | 'signal' | 'critical' | 'convention' | 'dashboard'} FlowType
 */

/**
 * @typedef {'setup' | 'question' | 'answer' | 'result' | 'summary'} FlowState
 * State machine states for learning flows
 */

/**
 * @typedef {Object} FlowInput
 * @property {import('./hand-types').Hand} hand - Player's 13 cards
 * @property {import('./hand-types').FourHands} [allHands] - All four hands (for DDS, reveal)
 * @property {import('./hand-types').Bid[]} [auction] - Completed or partial auction
 * @property {import('./hand-types').Contract} [contract] - Final contract if auction complete
 * @property {import('./hand-types').TrickPlay[]} [playHistory] - Trick-by-trick play record
 * @property {import('./hand-types').DDSResult} [ddsResults] - Double-dummy analysis
 * @property {string} [conventionTag] - For convention spotlight, replay
 * @property {PreviousAttempt} [previousAttempt] - For spaced repetition replay
 */

/**
 * @typedef {Object} PreviousAttempt
 * @property {*} playerAnswer - What the player answered before
 * @property {*} correctAnswer - What the correct answer was
 * @property {string} date - ISO date string of the attempt
 */

/**
 * @typedef {Object} FlowResult
 * @property {FlowType} flowType - Which flow this result is from
 * @property {string} handId - Unique identifier for the hand
 * @property {string} timestamp - ISO timestamp of completion
 * @property {Decision[]} decisions - Each scoreable decision
 * @property {number} overallScore - 0-100 score
 * @property {number} timeSpent - Milliseconds spent on the flow
 * @property {string[]} conventionTags - Which conventions were tested
 */

/**
 * @typedef {Object} Decision
 * @property {string} decisionId - Unique within the flow
 * @property {string} category - Skill category for tracking
 * @property {*} playerAnswer - What the player answered
 * @property {*} correctAnswer - The correct answer
 * @property {boolean} isCorrect - Whether the player was correct
 * @property {string} [explanation] - Explanation of the correct answer
 * @property {string} [conventionTag] - Related convention if any
 */

/**
 * @typedef {Object} ReviewItem
 * @property {string} handId - Reference to the original hand
 * @property {string} decisionPoint - Which decision in the hand
 * @property {string} conventionTag - Related convention
 * @property {1 | 3 | 7 | 14 | 30} interval - Days until next review
 * @property {string} nextReviewDate - ISO date string
 * @property {number} attempts - Number of times reviewed
 * @property {boolean} lastCorrect - Whether last attempt was correct
 */

/**
 * @typedef {Object} SkillStat
 * @property {string} category - Skill category name
 * @property {number} totalDecisions - Total decisions made
 * @property {number} correctDecisions - Correct decisions made
 * @property {number} accuracy7d - 7-day rolling accuracy (0-100)
 * @property {number} accuracy30d - 30-day rolling accuracy (0-100)
 * @property {string} lastPracticed - ISO timestamp
 */

/**
 * Get performance level based on percentage
 * @param {number} percentage - 0-100
 * @returns {'good' | 'medium' | 'weak'}
 */
export const getPerformanceLevel = (percentage) => {
  if (percentage >= 75) return 'good';
  if (percentage >= 60) return 'medium';
  return 'weak';
};

/**
 * Format a bid for display with suit symbol
 * @param {string} bid - Bid string like "1H", "3NT", "Pass"
 * @returns {string} Formatted bid like "1♥", "3NT", "Pass"
 */
export const formatBid = (bid) => {
  if (!bid || bid === 'Pass' || bid === 'X' || bid === 'XX') {
    return bid;
  }

  const suitMap = {
    'S': '♠',
    'H': '♥',
    'D': '♦',
    'C': '♣',
  };

  // Match patterns like "1H", "3NT", "2S"
  const match = bid.match(/^(\d)(S|H|D|C|NT)$/);
  if (match) {
    const [, level, strain] = match;
    if (strain === 'NT') return `${level}NT`;
    return `${level}${suitMap[strain]}`;
  }

  return bid;
};

/**
 * Generate a unique hand ID
 * @returns {string}
 */
export const generateHandId = () => {
  return `hand_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};
