/**
 * Analytics Service - API calls for the Common Mistake Detection System
 *
 * Provides methods for:
 * - Recording practice with error categorization
 * - Fetching dashboard data
 * - Getting practice recommendations
 * - Managing celebrations
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

/**
 * Record a practice hand with automatic error categorization
 * @param {Object} practiceData - Practice hand data
 * @returns {Promise<Object>} Response with XP earned, feedback, and user stats
 */
export async function recordPractice(practiceData) {
  const response = await fetch(`${API_BASE_URL}/api/practice/record`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(practiceData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to record practice');
  }

  return response.json();
}

/**
 * Get comprehensive dashboard data
 * @param {number} userId - User ID
 * @returns {Promise<Object>} Dashboard data with stats, insights, celebrations, recommendations
 */
export async function getDashboardData(userId) {
  const response = await fetch(`${API_BASE_URL}/api/analytics/dashboard?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch dashboard data');
  }

  return response.json();
}

/**
 * Get mistake patterns for user
 * @param {number} userId - User ID
 * @param {string} statusFilter - Optional status filter ('active', 'improving', 'resolved', 'needs_attention')
 * @returns {Promise<Object>} Mistake patterns
 */
export async function getMistakePatterns(userId, statusFilter = null) {
  let url = `${API_BASE_URL}/api/analytics/mistakes?user_id=${userId}`;
  if (statusFilter) {
    url += `&status=${statusFilter}`;
  }

  const response = await fetch(url);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch mistake patterns');
  }

  return response.json();
}

/**
 * Get celebrations for user
 * @param {number} userId - User ID
 * @param {boolean} pendingOnly - If true, only return unshown celebrations
 * @returns {Promise<Object>} Celebrations
 */
export async function getCelebrations(userId, pendingOnly = true) {
  const response = await fetch(
    `${API_BASE_URL}/api/analytics/celebrations?user_id=${userId}&pending_only=${pendingOnly}`
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch celebrations');
  }

  return response.json();
}

/**
 * Acknowledge a celebration
 * @param {number} milestoneId - Milestone ID
 * @returns {Promise<Object>} Success response
 */
export async function acknowledgeCelebration(milestoneId) {
  const response = await fetch(`${API_BASE_URL}/api/analytics/acknowledge-celebration`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ milestone_id: milestoneId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to acknowledge celebration');
  }

  return response.json();
}

/**
 * Get practice recommendations
 * @param {number} userId - User ID
 * @param {number} maxRecommendations - Maximum number of recommendations
 * @returns {Promise<Object>} Practice recommendations
 */
export async function getPracticeRecommendations(userId, maxRecommendations = 5) {
  const response = await fetch(
    `${API_BASE_URL}/api/practice/recommended?user_id=${userId}&max=${maxRecommendations}`
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch practice recommendations');
  }

  return response.json();
}

/**
 * Create a new user
 * @param {Object} userData - User data (username, email, display_name)
 * @returns {Promise<Object>} Created user
 */
export async function createUser(userData) {
  const response = await fetch(`${API_BASE_URL}/api/user/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to create user');
  }

  return response.json();
}

/**
 * Get user information and stats
 * @param {number} userId - User ID
 * @returns {Promise<Object>} User info and stats
 */
export async function getUserInfo(userId) {
  const response = await fetch(`${API_BASE_URL}/api/user/info?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch user info');
  }

  return response.json();
}

/**
 * Run full analysis for user (updates all pattern statuses)
 * @param {number} userId - User ID
 * @returns {Promise<Object>} Analysis results
 */
export async function runAnalysis(userId) {
  const response = await fetch(`${API_BASE_URL}/api/analytics/run-analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to run analysis');
  }

  return response.json();
}
