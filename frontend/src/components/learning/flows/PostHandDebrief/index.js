/**
 * PostHandDebrief Flow - Barrel Export
 *
 * Post-hand review screen showing all four hands, decision timeline,
 * and result summary.
 *
 * Usage:
 * import { PostHandDebrief, mockDebriefHands } from './flows/PostHandDebrief';
 */

import PostHandDebrief from './PostHandDebrief';
import DecisionTimeline from './DecisionTimeline';

export { PostHandDebrief, DecisionTimeline };

// Logic exports for testing
export {
  buildTimeline,
  calculateScore,
  countDecisions,
  buildFlowResult,
  formatContract,
  formatResult,
  getDeclarerName,
  wasHandSuccessful,
  getScoreStatus
} from './PostHandDebrief.logic';

// Mock data for development
export {
  mockDebriefHands,
  handPerfectBiddingPlayError,
  handBiddingMistake,
  handEverythingOptimal
} from './mockData';

export default PostHandDebrief;
