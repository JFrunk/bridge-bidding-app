/**
 * Learning Service - API calls for the Learning Mode system
 *
 * Provides methods for:
 * - Starting learning sessions
 * - Submitting answers and getting feedback
 * - Getting user learning status
 * - Interleaved review and level assessments
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

/**
 * Start a new learning session for a skill or convention
 * @param {number} userId - User ID
 * @param {string} topicId - Skill or convention ID
 * @param {string} topicType - 'skill' or 'convention'
 * @returns {Promise<Object>} Session info with first hand
 */
export async function startLearningSession(userId, topicId, topicType = 'skill') {
  const response = await fetch(`${API_BASE_URL}/api/learning/start-session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      topic_id: topicId,
      topic_type: topicType,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to start learning session');
  }

  return response.json();
}

/**
 * Submit an answer for the current hand
 * @param {Object} answerData - Answer data
 * @returns {Promise<Object>} Feedback and next hand
 */
export async function submitLearningAnswer(answerData) {
  const response = await fetch(`${API_BASE_URL}/api/learning/submit-answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(answerData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to submit answer');
  }

  return response.json();
}

/**
 * Get user's comprehensive learning status
 * @param {number} userId - User ID
 * @returns {Promise<Object>} Learning status with levels and progress
 */
export async function getLearningStatus(userId) {
  const response = await fetch(`${API_BASE_URL}/api/learning/status?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch learning status');
  }

  return response.json();
}

/**
 * Get interleaved review hands for a level
 * @param {number} userId - User ID
 * @param {number} level - Level number
 * @param {number} count - Number of hands (default 10)
 * @returns {Promise<Object>} Review session with mixed hands
 */
export async function getInterleavedReview(userId, level, count = 10) {
  const response = await fetch(
    `${API_BASE_URL}/api/learning/review?user_id=${userId}&level=${level}&count=${count}`
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch review hands');
  }

  return response.json();
}

/**
 * Get level assessment test
 * @param {number} userId - User ID
 * @param {number} level - Level number
 * @returns {Promise<Object>} Assessment with 20 mixed hands
 */
export async function getLevelAssessment(userId, level) {
  const response = await fetch(
    `${API_BASE_URL}/api/learning/level-assessment?user_id=${userId}&level=${level}`
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch level assessment');
  }

  return response.json();
}

/**
 * Get the full skill tree structure
 * @returns {Promise<Object>} Complete skill tree
 */
export async function getSkillTree() {
  const response = await fetch(`${API_BASE_URL}/api/skill-tree`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch skill tree');
  }

  return response.json();
}

/**
 * Get user's progress through the skill tree
 * @param {number} userId - User ID
 * @returns {Promise<Object>} User progress with level details
 */
export async function getSkillTreeProgress(userId) {
  const response = await fetch(`${API_BASE_URL}/api/skill-tree/progress?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch skill tree progress');
  }

  return response.json();
}

/**
 * Get curriculum summary
 * @returns {Promise<Object>} Curriculum summary with totals
 */
export async function getCurriculumSummary() {
  const response = await fetch(`${API_BASE_URL}/api/curriculum/summary`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch curriculum summary');
  }

  return response.json();
}
