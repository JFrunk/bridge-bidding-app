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
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
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
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
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
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
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
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
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
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
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

/**
 * Get user's progress on all skills
 * @param {number} userId - User ID
 * @returns {Promise<Object>} Skills with their status (not_started, in_progress, mastered)
 */
export async function getUserSkillProgress(userId) {
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
  const response = await fetch(`${API_BASE_URL}/api/user/skill-progress?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch skill progress');
  }

  return response.json();
}

/**
 * Submit user feedback about the learning experience
 * @param {Object} feedbackData - Feedback data
 * @param {string} feedbackData.type - Feedback type (issue, incorrect, confusing, suggestion)
 * @param {string} feedbackData.description - User's description
 * @param {string} feedbackData.context - Context ('learning' or 'freeplay')
 * @param {Object} feedbackData.contextData - Context-specific data
 * @returns {Promise<Object>} Submission result
 */
export async function submitFeedback(feedbackData) {
  const response = await fetch(`${API_BASE_URL}/api/submit-feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedbackData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to submit feedback');
  }

  return response.json();
}

// ==========================================
// PLAY SKILL LEARNING API FUNCTIONS
// ==========================================

/**
 * Get user's comprehensive play learning status
 * @param {number} userId - User ID
 * @returns {Promise<Object>} Play learning status with levels and progress
 */
export async function getPlayLearningStatus(userId) {
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
  const response = await fetch(`${API_BASE_URL}/api/learning/play-status?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch play learning status');
  }

  return response.json();
}

/**
 * Get the full play skill tree structure
 * @returns {Promise<Object>} Complete play skill tree
 */
export async function getPlaySkillTree() {
  const response = await fetch(`${API_BASE_URL}/api/play-skill-tree`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch play skill tree');
  }

  return response.json();
}

/**
 * Get user's progress through the play skill tree
 * @param {number} userId - User ID
 * @returns {Promise<Object>} User play progress with level details
 */
export async function getPlaySkillTreeProgress(userId) {
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
  const response = await fetch(`${API_BASE_URL}/api/play-skill-tree/progress?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch play skill tree progress');
  }

  return response.json();
}

/**
 * Get user's progress on all play skills
 * @param {number} userId - User ID
 * @returns {Promise<Object>} Play skills with their status (not_started, in_progress, mastered)
 */
export async function getUserPlayProgress(userId) {
  if (!userId || userId === 'null' || userId === 'undefined') throw new Error('user_id required');
  const response = await fetch(`${API_BASE_URL}/api/user/play-progress?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch play progress');
  }

  return response.json();
}

/**
 * Get play curriculum summary
 * @returns {Promise<Object>} Play curriculum summary with totals
 */
export async function getPlayCurriculumSummary() {
  const response = await fetch(`${API_BASE_URL}/api/play-curriculum/summary`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch play curriculum summary');
  }

  return response.json();
}

/**
 * Get a practice hand for a specific play skill
 * @param {string} skillId - Play skill ID
 * @param {number} level - Skill level (optional)
 * @returns {Promise<Object>} Practice hand with deal information
 */
export async function getPlayPracticeHand(skillId, level = null) {
  let url = `${API_BASE_URL}/api/play-skills/practice-hand?skill_id=${skillId}`;
  if (level !== null) {
    url += `&level=${level}`;
  }

  const response = await fetch(url);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch play practice hand');
  }

  return response.json();
}

/**
 * Record a play practice attempt
 * @param {Object} practiceData - Practice attempt data
 * @returns {Promise<Object>} Updated progress
 */
export async function recordPlayPractice(practiceData) {
  const response = await fetch(`${API_BASE_URL}/api/play-skills/record-practice`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(practiceData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to record play practice');
  }

  return response.json();
}

/**
 * Get list of available play skill generators
 * @returns {Promise<Object>} List of available generators
 */
export async function getAvailablePlayGenerators() {
  const response = await fetch(`${API_BASE_URL}/api/play-skills/available`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch available generators');
  }

  return response.json();
}
