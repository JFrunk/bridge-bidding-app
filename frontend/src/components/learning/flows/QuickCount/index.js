/**
 * QuickCount Flow - Barrel Export
 * Flow 5: Quick Count Drill
 *
 * A timed drill for practicing hand evaluation (HCP + distribution points).
 */

export { default as QuickCount } from './QuickCount';

export {
  // Constants
  LEVELS,
  LEVEL_NAMES,
  LEVEL_DESCRIPTIONS,
  HANDS_PER_ROUND,

  // Hand generation
  createDeck,
  shuffle,
  sortBySuitThenRank,
  generateRandomHand,
  generateHandData,

  // Point calculation
  calculateHCP,
  calculateLengthPoints,
  calculateShortnessPoints,
  calculateTotalPoints,
  getPointBreakdown,
  getSuitLengths,

  // Choice generation
  generateChoices,

  // Level 4 helpers
  getRandomTrumpSuit,
  shouldCountAsDummy,

  // Timer utilities
  formatTime,
  calculateAverageTime,

  // Scoring
  calculateScorePercentage,
  getPerformanceRating
} from './QuickCount.logic';
