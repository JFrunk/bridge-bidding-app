/**
 * GuessPartner Flow
 *
 * Barrel export for the Guess Partner's Hand learning flow.
 *
 * Usage:
 * import GuessPartner from '../flows/GuessPartner';
 * or
 * import { GuessPartner, FLOW_STATES, scoreAllEstimates } from '../flows/GuessPartner';
 */

export { default } from './GuessPartner';
export { default as GuessPartner } from './GuessPartner';

// Export logic utilities for testing or external use
export {
  FLOW_STATES,
  SHAPE_TYPES,
  calculateHCP,
  getSuitLengths,
  findLongestSuits,
  determineShape,
  scoreHCPEstimate,
  scoreLongestSuitEstimate,
  scoreSuitLengthEstimate,
  scoreShapeEstimate,
  scoreAllEstimates,
  getInitialEstimates,
  areEstimatesComplete,
  generateFlowResult,
} from './GuessPartner.logic';

// Export mock data for testing
export {
  ALL_SCENARIOS,
  SCENARIO_1NT_OPENING,
  SCENARIO_1S_GAME_FORCE,
  SCENARIO_COMPETITIVE,
  SCENARIO_SLAM_TRY,
  SCENARIO_BALANCE,
  getRandomScenario,
  getScenarioById,
} from './mockData';
