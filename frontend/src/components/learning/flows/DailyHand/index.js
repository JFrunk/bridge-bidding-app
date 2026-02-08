/**
 * DailyHand Flow - Barrel Export
 *
 * Daily Hand Challenge: One hand per day with streak tracking.
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

export { default } from './DailyHand';
export { default as DailyHand } from './DailyHand';

// Export logic utilities for testing or external use
export {
  FLOW_STATES,
  BID_LEVELS,
  STRAINS,
  STRAIN_SYMBOLS,
  getTodayString,
  createSeededRandom,
  generateDailyHand,
  calculateHCP,
  getDailyStorage,
  saveDailyStorage,
  isTodayCompleted,
  getCurrentStreak,
  calculateNewStreak,
  generateStreakCalendar,
  isBidLegal,
  getLegalBids,
  isAuctionComplete,
  isAllPass,
  getContractFromAuction,
  getBiddingOrder,
  getCurrentBidder,
  getAIBid,
  getAIPlay,
  getDDSResult,
  buildFlowResult,
  getInitialState,
  dailyHandReducer,
} from './DailyHand.logic';
