/**
 * Spaced Repetition Algorithm for Bidding Replay
 *
 * Implements a simplified SM-2 style algorithm with fixed intervals.
 * Items progress through intervals when answered correctly, reset when wrong.
 *
 * Storage: localStorage keys 'mbb-review-queue' and 'mbb-hand-history'
 */

// Review intervals in days
export const INTERVALS = [1, 3, 7, 14, 30];

// Number of consecutive correct answers at max interval to "retire" an item
export const MASTERY_THRESHOLD = 3;

// localStorage keys
const STORAGE_KEYS = {
  REVIEW_QUEUE: 'mbb-review-queue',
  HAND_HISTORY: 'mbb-hand-history'
};

/**
 * @typedef {Object} ReviewItem
 * @property {string} handId - Reference to the original hand
 * @property {string} decisionPoint - Which decision in the hand (e.g., "opening", "response")
 * @property {string} conventionTag - Related convention (e.g., "stayman", "jacoby")
 * @property {string} category - Skill category for grouping (e.g., "responses", "rebids")
 * @property {number} intervalIndex - Current index in INTERVALS array (0-4)
 * @property {string} nextReviewDate - ISO date string of next review
 * @property {number} attempts - Number of times reviewed
 * @property {number} correctStreak - Consecutive correct answers at current interval
 * @property {boolean} lastCorrect - Whether last attempt was correct
 * @property {string} previousBid - What the player bid last time
 * @property {string} correctBid - The correct bid
 * @property {Object} handData - The hand and auction data for replay
 */

/**
 * Get today's date as ISO string (date only, no time)
 * @returns {string}
 */
export const getToday = () => {
  return new Date().toISOString().split('T')[0];
};

/**
 * Add days to a date
 * @param {string} dateStr - ISO date string
 * @param {number} days - Days to add
 * @returns {string} - New ISO date string
 */
export const addDays = (dateStr, days) => {
  const date = new Date(dateStr);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
};

/**
 * Calculate days overdue (negative if not yet due)
 * @param {string} reviewDate - ISO date string
 * @returns {number}
 */
export const getDaysOverdue = (reviewDate) => {
  const today = new Date(getToday());
  const review = new Date(reviewDate);
  const diffTime = today - review;
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
};

/**
 * Get current interval in days for a review item
 * @param {ReviewItem} item
 * @returns {number}
 */
export const getCurrentInterval = (item) => {
  return INTERVALS[item.intervalIndex] || INTERVALS[0];
};

/**
 * Calculate next review based on correctness
 * @param {ReviewItem} item - Current item state
 * @param {boolean} isCorrect - Whether the answer was correct
 * @returns {ReviewItem} - Updated item
 */
export const calculateNextReview = (item, isCorrect) => {
  const updated = { ...item };
  updated.attempts += 1;
  updated.lastCorrect = isCorrect;

  if (isCorrect) {
    updated.correctStreak += 1;

    // Check for mastery (3 correct at 30-day interval)
    if (updated.intervalIndex === INTERVALS.length - 1 &&
        updated.correctStreak >= MASTERY_THRESHOLD) {
      updated.mastered = true;
      updated.nextReviewDate = null; // Retired
    } else if (updated.intervalIndex < INTERVALS.length - 1) {
      // Advance to next interval
      updated.intervalIndex += 1;
      updated.correctStreak = 0;
      const nextInterval = INTERVALS[updated.intervalIndex];
      updated.nextReviewDate = addDays(getToday(), nextInterval);
    } else {
      // Stay at max interval
      updated.nextReviewDate = addDays(getToday(), INTERVALS[INTERVALS.length - 1]);
    }
  } else {
    // Reset to first interval
    updated.intervalIndex = 0;
    updated.correctStreak = 0;
    updated.nextReviewDate = addDays(getToday(), INTERVALS[0]);
  }

  return updated;
};

/**
 * Load review queue from localStorage
 * @returns {ReviewItem[]}
 */
export const loadReviewQueue = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.REVIEW_QUEUE);
    return data ? JSON.parse(data) : [];
  } catch (e) {
    console.error('Failed to load review queue:', e);
    return [];
  }
};

/**
 * Save review queue to localStorage
 * @param {ReviewItem[]} queue
 */
export const saveReviewQueue = (queue) => {
  try {
    localStorage.setItem(STORAGE_KEYS.REVIEW_QUEUE, JSON.stringify(queue));
  } catch (e) {
    console.error('Failed to save review queue:', e);
  }
};

/**
 * Load hand history from localStorage
 * @returns {Object[]}
 */
export const loadHandHistory = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.HAND_HISTORY);
    return data ? JSON.parse(data) : [];
  } catch (e) {
    console.error('Failed to load hand history:', e);
    return [];
  }
};

/**
 * Save hand history to localStorage
 * @param {Object[]} history
 */
export const saveHandHistory = (history) => {
  try {
    localStorage.setItem(STORAGE_KEYS.HAND_HISTORY, JSON.stringify(history));
  } catch (e) {
    console.error('Failed to save hand history:', e);
  }
};

/**
 * Add an item to the review queue (for missed bidding decisions)
 * @param {Object} params
 * @param {string} params.handId
 * @param {string} params.decisionPoint
 * @param {string} params.conventionTag
 * @param {string} params.category
 * @param {string} params.previousBid
 * @param {string} params.correctBid
 * @param {Object} params.handData
 * @returns {ReviewItem}
 */
export const addToReviewQueue = ({
  handId,
  decisionPoint,
  conventionTag,
  category,
  previousBid,
  correctBid,
  handData
}) => {
  const queue = loadReviewQueue();

  // Check if this exact decision point already exists
  const existingIndex = queue.findIndex(
    item => item.handId === handId && item.decisionPoint === decisionPoint
  );

  if (existingIndex !== -1) {
    // Update existing item - reset it since they got it wrong again
    queue[existingIndex].intervalIndex = 0;
    queue[existingIndex].correctStreak = 0;
    queue[existingIndex].nextReviewDate = addDays(getToday(), 1);
    queue[existingIndex].previousBid = previousBid;
    saveReviewQueue(queue);
    return queue[existingIndex];
  }

  // Create new review item
  const newItem = {
    handId,
    decisionPoint,
    conventionTag,
    category,
    intervalIndex: 0,
    nextReviewDate: addDays(getToday(), 1),
    attempts: 0,
    correctStreak: 0,
    lastCorrect: false,
    previousBid,
    correctBid,
    handData,
    createdAt: new Date().toISOString()
  };

  queue.push(newItem);
  saveReviewQueue(queue);
  return newItem;
};

/**
 * Update a review item after a review session
 * @param {string} handId
 * @param {string} decisionPoint
 * @param {boolean} isCorrect
 * @returns {ReviewItem|null}
 */
export const updateReviewItem = (handId, decisionPoint, isCorrect) => {
  const queue = loadReviewQueue();
  const index = queue.findIndex(
    item => item.handId === handId && item.decisionPoint === decisionPoint
  );

  if (index === -1) return null;

  const updated = calculateNextReview(queue[index], isCorrect);

  if (updated.mastered) {
    // Remove from queue
    queue.splice(index, 1);
  } else {
    queue[index] = updated;
  }

  saveReviewQueue(queue);
  return updated;
};

/**
 * Get items due for review today
 * Sorted by: overdue first, then by lowest accuracy
 * @param {number} limit - Maximum items to return
 * @returns {ReviewItem[]}
 */
export const getDueItems = (limit = 5) => {
  const queue = loadReviewQueue();
  const today = getToday();

  // Filter to items that are due (nextReviewDate <= today)
  const dueItems = queue.filter(item => {
    if (!item.nextReviewDate) return false;
    return item.nextReviewDate <= today;
  });

  // Sort by: most overdue first, then by accuracy (worst first)
  dueItems.sort((a, b) => {
    const overdueA = getDaysOverdue(a.nextReviewDate);
    const overdueB = getDaysOverdue(b.nextReviewDate);

    if (overdueA !== overdueB) {
      return overdueB - overdueA; // More overdue first
    }

    // Calculate accuracy (attempts might be 0)
    const accuracyA = a.attempts > 0 ? (a.correctStreak / a.attempts) : 0;
    const accuracyB = b.attempts > 0 ? (b.correctStreak / b.attempts) : 0;

    return accuracyA - accuracyB; // Lower accuracy first
  });

  return dueItems.slice(0, limit);
};

/**
 * Get review queue statistics
 * @returns {Object}
 */
export const getQueueStats = () => {
  const queue = loadReviewQueue();
  const today = getToday();

  const dueToday = queue.filter(item =>
    item.nextReviewDate && item.nextReviewDate <= today
  ).length;

  const total = queue.length;

  // Group by category
  const byCategory = queue.reduce((acc, item) => {
    const cat = item.category || 'other';
    if (!acc[cat]) {
      acc[cat] = { total: 0, due: 0 };
    }
    acc[cat].total += 1;
    if (item.nextReviewDate && item.nextReviewDate <= today) {
      acc[cat].due += 1;
    }
    return acc;
  }, {});

  // Calculate average accuracy
  const withAttempts = queue.filter(item => item.attempts > 0);
  const avgAccuracy = withAttempts.length > 0
    ? withAttempts.reduce((sum, item) => {
        const correct = item.lastCorrect ? 1 : 0;
        return sum + (correct / item.attempts);
      }, 0) / withAttempts.length
    : 0;

  return {
    total,
    dueToday,
    byCategory,
    avgAccuracy: Math.round(avgAccuracy * 100)
  };
};

/**
 * Clear all review data (for testing/reset)
 */
export const clearAllReviewData = () => {
  localStorage.removeItem(STORAGE_KEYS.REVIEW_QUEUE);
  localStorage.removeItem(STORAGE_KEYS.HAND_HISTORY);
};
