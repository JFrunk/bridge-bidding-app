/**
 * DefensiveSignal Flow - Barrel Export
 * Flow 7: Defensive Signal Quiz
 */

export { default as DefensiveSignal } from './DefensiveSignal';
export {
  SIGNAL_TYPE_INFO,
  evaluateSignal,
  getCardsInSuit,
  getDisabledIndices,
  calculateSummary,
  buildFlowResult,
} from './DefensiveSignal.logic';
export {
  SIGNAL_SITUATIONS,
  getSituationsByType,
  getSituationsByLevel,
  getShuffledSituations,
} from './mockData';
