/**
 * ConventionSpotlight Flow - Barrel Export
 * Flow 9: Convention Spotlight
 *
 * Provides focused learning for bridge conventions including:
 * - Convention library with mastery tracking
 * - Quick reference cards
 * - Drill hands for practice
 * - Progress summaries
 */

export { default as ConventionSpotlight } from './ConventionSpotlight';

export {
  FLOW_STATES,
  INITIAL_STATE,
  evaluateAnswer,
  createDecision,
  generateFlowResult,
  getSessionSummary,
  formatTimeSpent,
  hasMoreHands,
  getYesNoChoices,
  getRelatedConventions,
  getConventionMasteryLevel,
  flowReducer,
} from './ConventionSpotlight.logic';

export {
  CONVENTIONS,
  CONVENTION_CATEGORIES,
  QUESTION_TYPES,
  getConventionById,
  getConventionsByCategory,
  getDrillHand,
} from './conventions.data';
