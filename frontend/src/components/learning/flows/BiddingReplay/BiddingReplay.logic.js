/**
 * BiddingReplay Logic
 *
 * Evaluation logic for rebid decisions in the spaced repetition flow.
 */

import { formatBid } from '../../types/flow-types';
import {
  updateReviewItem,
  INTERVALS
} from './spacedRepetition';

/**
 * Normalize a bid for comparison
 * Handles various formats: "1H", "1♥", "1 H", etc.
 * @param {string} bid
 * @returns {string}
 */
export const normalizeBid = (bid) => {
  if (!bid) return '';

  // Convert to uppercase and remove spaces
  let normalized = bid.toUpperCase().replace(/\s+/g, '');

  // Convert suit symbols to letters
  normalized = normalized
    .replace(/♠/g, 'S')
    .replace(/♥/g, 'H')
    .replace(/♦/g, 'D')
    .replace(/♣/g, 'C');

  return normalized;
};

/**
 * Check if two bids are equivalent
 * @param {string} bid1
 * @param {string} bid2
 * @returns {boolean}
 */
export const bidsMatch = (bid1, bid2) => {
  return normalizeBid(bid1) === normalizeBid(bid2);
};

/**
 * Evaluate a rebid attempt
 * @param {Object} params
 * @param {string} params.userBid - The bid the user made
 * @param {string} params.correctBid - The correct bid
 * @param {Object} params.reviewItem - The review item being tested
 * @returns {Object} Evaluation result
 */
export const evaluateRebid = ({ userBid, correctBid, reviewItem }) => {
  const isCorrect = bidsMatch(userBid, correctBid);

  // Update the review item in storage
  const updatedItem = updateReviewItem(
    reviewItem.handId,
    reviewItem.decisionPoint,
    isCorrect
  );

  // Calculate new interval info
  let nextReviewInfo;
  if (updatedItem) {
    if (updatedItem.mastered) {
      nextReviewInfo = {
        status: 'mastered',
        message: 'Mastered! This hand has been retired.',
        intervalDays: null
      };
    } else {
      const intervalDays = INTERVALS[updatedItem.intervalIndex];
      nextReviewInfo = {
        status: isCorrect ? 'advanced' : 'reset',
        message: isCorrect
          ? `Great! Next review in ${intervalDays} day${intervalDays !== 1 ? 's' : ''}.`
          : `Let's try again tomorrow.`,
        intervalDays,
        nextDate: updatedItem.nextReviewDate
      };
    }
  }

  return {
    isCorrect,
    userBid: formatBid(userBid),
    correctBid: formatBid(correctBid),
    previousBid: formatBid(reviewItem.previousBid),
    reviewItem: updatedItem,
    nextReviewInfo,
    explanation: getExplanation(reviewItem, isCorrect)
  };
};

/**
 * Get explanation for the correct bid
 * @param {Object} reviewItem
 * @param {boolean} isCorrect
 * @returns {string}
 */
const getExplanation = (reviewItem, isCorrect) => {
  const { conventionTag } = reviewItem;
  const correctBid = formatBid(reviewItem.correctBid);

  // Convention-specific explanations
  const explanations = {
    stayman: `With a 4-card major and game values, use Stayman (2C) to find a 4-4 major fit.`,
    jacoby: `With 5+ cards in a major, use a Jacoby Transfer. Bid the suit below your major.`,
    blackwood: `Blackwood responses: 5C = 0/4 aces, 5D = 1 ace, 5H = 2 aces, 5S = 3 aces.`,
    overcalls: `With support for partner's overcall, raise to show your values and fit.`,
    rebids: `As opener with extra values and a fit, invite game with a jump raise.`,
    opening: `With balanced distribution and 15-17 HCP, open 1NT rather than a suit.`
  };

  const base = explanations[conventionTag] || `The correct bid is ${correctBid}.`;

  if (isCorrect) {
    return `Correct! ${base}`;
  }

  return base;
};

/**
 * Build the info strip message
 * @param {Object} reviewItem
 * @returns {string}
 */
export const buildInfoStripMessage = (reviewItem) => {
  const previousBid = formatBid(reviewItem.previousBid);
  const correctBid = formatBid(reviewItem.correctBid);

  return {
    prefix: 'Last time you bid',
    previousBid,
    middle: 'The correct bid was',
    correctBid,
    suffix: 'Can you get it right?'
  };
};

/**
 * Calculate session statistics
 * @param {Object[]} results - Array of evaluation results
 * @returns {Object}
 */
export const calculateSessionStats = (results) => {
  const total = results.length;
  const correct = results.filter(r => r.isCorrect).length;

  // Group by category
  const byCategory = results.reduce((acc, result) => {
    const category = result.reviewItem?.category || 'other';
    if (!acc[category]) {
      acc[category] = { total: 0, correct: 0 };
    }
    acc[category].total += 1;
    if (result.isCorrect) {
      acc[category].correct += 1;
    }
    return acc;
  }, {});

  // Calculate category trends (simplified - would need historical data for real trends)
  const categoryBreakdown = Object.entries(byCategory).map(([category, stats]) => ({
    category,
    total: stats.total,
    correct: stats.correct,
    percentage: Math.round((stats.correct / stats.total) * 100),
    // Trend would be calculated from historical data
    trend: stats.correct === stats.total ? 'up' : stats.correct === 0 ? 'down' : 'flat'
  }));

  // Next review dates
  const nextReviews = results
    .filter(r => r.reviewItem?.nextReviewDate)
    .map(r => ({
      handId: r.reviewItem.handId,
      category: r.reviewItem.category,
      nextDate: r.reviewItem.nextReviewDate,
      intervalDays: INTERVALS[r.reviewItem.intervalIndex]
    }))
    .sort((a, b) => a.nextDate.localeCompare(b.nextDate));

  return {
    total,
    correct,
    percentage: total > 0 ? Math.round((correct / total) * 100) : 0,
    categoryBreakdown,
    nextReviews,
    masteredCount: results.filter(r => r.reviewItem?.mastered).length
  };
};

/**
 * Get a hint for the current hand
 * @param {Object} reviewItem
 * @returns {string}
 */
export const getHint = (reviewItem) => {
  const { conventionTag } = reviewItem;

  const hints = {
    stayman: 'Consider: Do you have a 4-card major? How many points?',
    jacoby: 'Consider: How long is your major suit? What bid shows that suit?',
    blackwood: 'Consider: How many aces do you have? What response shows that?',
    overcalls: 'Consider: How many cards do you have in partner\'s suit?',
    rebids: 'Consider: What is your point range? Do you have extra values?',
    opening: 'Consider: Is your hand balanced? What is your HCP range?'
  };

  return hints[conventionTag] || 'Think about what this auction shows and what partner needs to know.';
};
