/**
 * TrainingDashboard Flow - Barrel Export
 * Flow 10: Training Dashboard (Analytics)
 */

export { default as TrainingDashboard } from './TrainingDashboard';
export {
  calculateDashboardData,
  calculateSummaryStats,
  calculateSkillStats,
  calculateConventionStats,
  generateRecommendations,
  getRecentActivity,
  generateStreakCalendar,
  filterByPeriod,
  getFlowResults,
  getStreakData,
  getReviewQueue,
  TIME_PERIODS,
  SKILL_CATEGORIES,
  CONVENTIONS,
  STORAGE_KEYS,
  getFlowTypeName,
} from './TrainingDashboard.logic';
