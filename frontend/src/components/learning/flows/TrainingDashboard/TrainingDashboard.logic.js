/**
 * TrainingDashboard.logic.js
 *
 * Data aggregation, statistics calculation, and recommendation logic
 * for the Training Dashboard (Flow 10).
 *
 * This module reads from localStorage and computes analytics for display.
 */

/**
 * localStorage keys for learning data
 */
export const STORAGE_KEYS = {
  FLOW_RESULTS: 'mbb-flow-results',
  STREAK: 'mbb-streak',
  REVIEW_QUEUE: 'mbb-review-queue',
};

/**
 * Time period filters
 * @enum {string}
 */
export const TIME_PERIODS = {
  WEEK: '7d',
  MONTH: '30d',
  ALL: 'all',
};

/**
 * Skill category definitions with display names and flow mappings
 */
export const SKILL_CATEGORIES = {
  'opening-bids': { name: 'Opening Bids', flowType: 'daily' },
  'responses': { name: 'Responses', flowType: 'daily' },
  'rebids': { name: 'Rebids', flowType: 'daily' },
  'competitive-bidding': { name: 'Competitive Bidding', flowType: 'daily' },
  'slam-bidding': { name: 'Slam Bidding', flowType: 'convention' },
  'opening-leads': { name: 'Opening Leads', flowType: 'lead' },
  'defensive-play': { name: 'Defensive Play', flowType: 'signal' },
  'declarer-play': { name: 'Declarer Play', flowType: 'count' },
  'hand-evaluation': { name: 'Hand Evaluation', flowType: 'guess' },
  'conventions': { name: 'Conventions', flowType: 'convention' },
};

/**
 * Convention definitions with display names
 */
export const CONVENTIONS = {
  'stayman': 'Stayman',
  'jacoby': 'Jacoby Transfer',
  'blackwood': 'Blackwood',
  'gerber': 'Gerber',
  'negative-double': 'Negative Double',
  'takeout-double': 'Takeout Double',
  'michaels': 'Michaels Cuebid',
  'unusual-2nt': 'Unusual 2NT',
};

/**
 * Get flow results from localStorage
 * @returns {Array<Object>} Array of FlowResult objects
 */
export const getFlowResults = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.FLOW_RESULTS);
    return stored ? JSON.parse(stored) : [];
  } catch (e) {
    console.error('Error reading flow results:', e);
    return [];
  }
};

/**
 * Get streak data from localStorage
 * @returns {Object} Streak data { currentStreak, longestStreak, lastDate }
 */
export const getStreakData = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.STREAK);
    return stored ? JSON.parse(stored) : { currentStreak: 0, longestStreak: 0, lastDate: null };
  } catch (e) {
    console.error('Error reading streak data:', e);
    return { currentStreak: 0, longestStreak: 0, lastDate: null };
  }
};

/**
 * Get review queue from localStorage
 * @returns {Array<Object>} Array of ReviewItem objects
 */
export const getReviewQueue = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.REVIEW_QUEUE);
    return stored ? JSON.parse(stored) : [];
  } catch (e) {
    console.error('Error reading review queue:', e);
    return [];
  }
};

/**
 * Filter results by time period
 * @param {Array<Object>} results - Flow results
 * @param {string} period - Time period ('7d', '30d', 'all')
 * @returns {Array<Object>} Filtered results
 */
export const filterByPeriod = (results, period) => {
  if (period === TIME_PERIODS.ALL) {
    return results;
  }

  const now = new Date();
  const days = period === TIME_PERIODS.WEEK ? 7 : 30;
  const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

  return results.filter(r => new Date(r.timestamp) >= cutoff);
};

/**
 * Calculate overall summary statistics
 * @param {Array<Object>} results - Filtered flow results
 * @param {Array<Object>} allResults - All flow results (for trend calculation)
 * @param {Object} streakData - Streak data from localStorage
 * @returns {Object} Summary stats { handsPlayed, streak, accuracy, trends }
 */
export const calculateSummaryStats = (results, allResults, streakData) => {
  const handsPlayed = results.length;

  // Calculate overall accuracy
  let totalDecisions = 0;
  let correctDecisions = 0;
  results.forEach(r => {
    if (r.decisions) {
      totalDecisions += r.decisions.length;
      correctDecisions += r.decisions.filter(d => d.isCorrect).length;
    }
  });
  const accuracy = totalDecisions > 0 ? Math.round((correctDecisions / totalDecisions) * 100) : 0;

  // Calculate trend (compare last 7 days to previous 7 days)
  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

  const thisWeek = allResults.filter(r => new Date(r.timestamp) >= weekAgo);
  const lastWeek = allResults.filter(r => {
    const date = new Date(r.timestamp);
    return date >= twoWeeksAgo && date < weekAgo;
  });

  const getAccuracy = (items) => {
    let total = 0;
    let correct = 0;
    items.forEach(r => {
      if (r.decisions) {
        total += r.decisions.length;
        correct += r.decisions.filter(d => d.isCorrect).length;
      }
    });
    return total > 0 ? (correct / total) * 100 : 0;
  };

  const thisWeekAccuracy = getAccuracy(thisWeek);
  const lastWeekAccuracy = getAccuracy(lastWeek);
  const accuracyDiff = thisWeekAccuracy - lastWeekAccuracy;

  let accuracyTrend = 'stable';
  if (accuracyDiff > 5) accuracyTrend = 'improving';
  else if (accuracyDiff < -5) accuracyTrend = 'declining';

  return {
    handsPlayed,
    streak: streakData.currentStreak || 0,
    longestStreak: streakData.longestStreak || 0,
    accuracy,
    accuracyTrend,
    accuracyDiff: Math.round(accuracyDiff),
  };
};

/**
 * Calculate skill breakdown statistics
 * @param {Array<Object>} results - Filtered flow results
 * @returns {Array<Object>} Skill stats sorted by accuracy
 */
export const calculateSkillStats = (results) => {
  const categoryStats = {};

  // Initialize all categories
  Object.entries(SKILL_CATEGORIES).forEach(([key, value]) => {
    categoryStats[key] = {
      category: key,
      name: value.name,
      flowType: value.flowType,
      totalDecisions: 0,
      correctDecisions: 0,
      lastPracticed: null,
    };
  });

  // Aggregate decisions by category
  results.forEach(result => {
    if (!result.decisions) return;

    result.decisions.forEach(decision => {
      const category = decision.category || 'conventions';
      if (categoryStats[category]) {
        categoryStats[category].totalDecisions++;
        if (decision.isCorrect) {
          categoryStats[category].correctDecisions++;
        }
        const resultDate = new Date(result.timestamp);
        if (!categoryStats[category].lastPracticed || resultDate > new Date(categoryStats[category].lastPracticed)) {
          categoryStats[category].lastPracticed = result.timestamp;
        }
      }
    });
  });

  // Calculate accuracy and convert to array
  return Object.values(categoryStats)
    .map(stat => ({
      ...stat,
      accuracy: stat.totalDecisions > 0
        ? Math.round((stat.correctDecisions / stat.totalDecisions) * 100)
        : null,
    }))
    .filter(stat => stat.totalDecisions > 0) // Only include practiced skills
    .sort((a, b) => a.accuracy - b.accuracy); // Sort by accuracy ascending (weakest first)
};

/**
 * Calculate convention mastery statistics
 * @param {Array<Object>} results - Filtered flow results
 * @returns {Array<Object>} Convention stats sorted by accuracy
 */
export const calculateConventionStats = (results) => {
  const conventionStats = {};

  // Initialize conventions
  Object.entries(CONVENTIONS).forEach(([key, name]) => {
    conventionStats[key] = {
      tag: key,
      name,
      totalDecisions: 0,
      correctDecisions: 0,
    };
  });

  // Aggregate by convention tag
  results.forEach(result => {
    if (!result.conventionTags || !result.decisions) return;

    result.conventionTags.forEach(tag => {
      if (conventionStats[tag]) {
        result.decisions.forEach(decision => {
          if (decision.conventionTag === tag) {
            conventionStats[tag].totalDecisions++;
            if (decision.isCorrect) {
              conventionStats[tag].correctDecisions++;
            }
          }
        });
      }
    });
  });

  // Calculate accuracy and convert to array
  return Object.values(conventionStats)
    .map(stat => ({
      ...stat,
      accuracy: stat.totalDecisions > 0
        ? Math.round((stat.correctDecisions / stat.totalDecisions) * 100)
        : null,
    }))
    .filter(stat => stat.totalDecisions > 0) // Only include practiced conventions
    .sort((a, b) => (b.accuracy || 0) - (a.accuracy || 0)); // Sort by accuracy descending
};

/**
 * Generate practice recommendations based on weakest areas
 * @param {Array<Object>} skillStats - Skill breakdown stats
 * @param {Array<Object>} conventionStats - Convention stats
 * @returns {Array<Object>} Recommendations with flowType and description
 */
export const generateRecommendations = (skillStats, conventionStats) => {
  const recommendations = [];
  const MIN_DECISIONS = 5; // Minimum decisions needed to recommend

  // Find 2 weakest skill categories with enough data
  const weakSkills = skillStats
    .filter(s => s.totalDecisions >= MIN_DECISIONS && s.accuracy !== null)
    .slice(0, 2);

  weakSkills.forEach(skill => {
    let description;
    let priority;

    if (skill.accuracy < 50) {
      description = `Your ${skill.name.toLowerCase()} accuracy is ${skill.accuracy}%. Focus practice here to improve.`;
      priority = 'high';
    } else if (skill.accuracy < 70) {
      description = `${skill.name} at ${skill.accuracy}% could use some work.`;
      priority = 'medium';
    } else {
      description = `Keep practicing ${skill.name.toLowerCase()} to maintain your ${skill.accuracy}% accuracy.`;
      priority = 'low';
    }

    recommendations.push({
      category: skill.category,
      name: skill.name,
      flowType: skill.flowType,
      accuracy: skill.accuracy,
      description,
      priority,
    });
  });

  // Add convention recommendation if any are weak
  const weakConventions = conventionStats.filter(c => c.accuracy !== null && c.accuracy < 70);
  if (weakConventions.length > 0) {
    const weakest = weakConventions[weakConventions.length - 1]; // Already sorted desc, get last
    recommendations.push({
      category: 'conventions',
      name: weakest.name,
      flowType: 'convention',
      accuracy: weakest.accuracy,
      description: `Your ${weakest.name} recognition needs practice at ${weakest.accuracy}%.`,
      priority: weakest.accuracy < 50 ? 'high' : 'medium',
      conventionTag: weakest.tag,
    });
  }

  // Sort by priority
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  recommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

  return recommendations.slice(0, 2); // Return top 2 recommendations
};

/**
 * Get recent activity for display
 * @param {Array<Object>} results - Flow results
 * @param {number} limit - Maximum items to return
 * @returns {Array<Object>} Recent activity items
 */
export const getRecentActivity = (results, limit = 5) => {
  return results
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, limit)
    .map(result => ({
      flowType: result.flowType,
      timestamp: result.timestamp,
      score: result.overallScore,
      decisionsCount: result.decisions?.length || 0,
      correctCount: result.decisions?.filter(d => d.isCorrect).length || 0,
    }));
};

/**
 * Generate 7-day streak calendar data
 * @param {Array<Object>} results - All flow results
 * @returns {Array<Object>} Days array for StreakCalendar component
 */
export const generateStreakCalendar = (results) => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const days = [];

  // Generate last 7 days including today
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    const dateStr = date.toISOString().split('T')[0];
    const dayResults = results.filter(r => {
      const resultDate = new Date(r.timestamp).toISOString().split('T')[0];
      return resultDate === dateStr;
    });

    const isToday = i === 0;
    let status;
    if (isToday) {
      status = dayResults.length > 0 ? 'done' : 'today';
    } else {
      status = dayResults.length > 0 ? 'done' : 'future';
    }

    days.push({
      label: dayLabels[date.getDay()],
      status,
      count: dayResults.length,
    });
  }

  return days;
};

/**
 * Flow type display names for recent activity
 */
export const FLOW_TYPE_NAMES = {
  daily: 'Daily Challenge',
  lead: 'Opening Lead',
  guess: 'Partner Guess',
  debrief: 'Post-Hand Debrief',
  count: 'Counting Trainer',
  replay: 'Replay Hand',
  signal: 'Defensive Signals',
  critical: 'Critical Decision',
  convention: 'Convention Practice',
  dashboard: 'Dashboard',
};

/**
 * Get display name for flow type
 * @param {string} flowType - Flow type key
 * @returns {string} Display name
 */
export const getFlowTypeName = (flowType) => {
  return FLOW_TYPE_NAMES[flowType] || flowType;
};

/**
 * Calculate all dashboard data
 * @param {string} period - Time period filter
 * @returns {Object} Complete dashboard data
 */
export const calculateDashboardData = (period = TIME_PERIODS.WEEK) => {
  const allResults = getFlowResults();
  const filteredResults = filterByPeriod(allResults, period);
  const streakData = getStreakData();
  const reviewQueue = getReviewQueue();

  const summary = calculateSummaryStats(filteredResults, allResults, streakData);
  const skillStats = calculateSkillStats(filteredResults);
  const conventionStats = calculateConventionStats(filteredResults);
  const recommendations = generateRecommendations(skillStats, conventionStats);
  const recentActivity = getRecentActivity(allResults, 5);
  const streakCalendar = generateStreakCalendar(allResults);

  return {
    summary,
    skillStats,
    conventionStats,
    recommendations,
    recentActivity,
    streakCalendar,
    reviewQueueCount: reviewQueue.length,
    dueForReview: reviewQueue.filter(item => {
      return new Date(item.nextReviewDate) <= new Date();
    }).length,
  };
};
