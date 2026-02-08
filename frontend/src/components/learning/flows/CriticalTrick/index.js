/**
 * CriticalTrick Flow - Barrel Export
 * Flow 8: Play the Critical Trick
 *
 * A declarer play training flow for critical decision points.
 */

export { default as CriticalTrick } from './CriticalTrick';
export { default as TrickBar } from './TrickBar';
export {
  evaluatePlan,
  getCorrectPlan,
  parseContract,
  generateFlowResult,
  getDifficultyRating,
  formatSituationText,
  getTechniqueDescription
} from './CriticalTrick.logic';
export {
  CRITICAL_TRICK_PROBLEMS,
  getRandomProblem,
  getProblemById,
  getAllProblemIds
} from './mockData';
