/**
 * Hand Review - Shared Constants and Utilities
 *
 * Extracted from HandReviewModal/HandReviewPage to eliminate duplication.
 * Used by all hand review components.
 */

// Rating colors and labels for feedback display
export const RATING_CONFIG = {
  optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '\u2713', label: 'Optimal' },
  good: { color: '#3b82f6', bgColor: '#eff6ff', icon: '\u25cb', label: 'Good' },
  acceptable: { color: '#3b82f6', bgColor: '#eff6ff', icon: '\u25cb', label: 'Acceptable' },
  suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
  suboptimal_signal: { color: '#ed8936', bgColor: '#fffaf0', icon: '\u26a0', label: 'Suboptimal Signal' },
  blunder: { color: '#dc2626', bgColor: '#fef2f2', icon: '\u2717', label: 'Blunder' },
  error: { color: '#dc2626', bgColor: '#fef2f2', icon: '\u2717', label: 'Error' }
};

// Position labels mapping
export const POSITION_LABELS = {
  N: 'North',
  E: 'East',
  S: 'South',
  W: 'West'
};

// Rank order for card sorting (high to low)
export const RANK_ORDER = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];

// Rank display mapping (T -> 10)
export const RANK_DISPLAY = {
  'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10',
  '10': '10', '9': '9', '8': '8', '7': '7', '6': '6',
  '5': '5', '4': '4', '3': '3', '2': '2'
};

/**
 * Get suit order based on trump strain
 * Trump suit comes first for easier visual scanning
 */
export const getSuitOrder = (trumpStrain) => {
  if (!trumpStrain || trumpStrain === 'NT') {
    return ['\u2660', '\u2665', '\u2663', '\u2666'];
  }
  const strainToSuit = { 'S': '\u2660', 'H': '\u2665', 'D': '\u2666', 'C': '\u2663' };
  const trumpSuit = strainToSuit[trumpStrain] || trumpStrain;
  if (trumpSuit === '\u2665') return ['\u2665', '\u2660', '\u2666', '\u2663'];
  if (trumpSuit === '\u2666') return ['\u2666', '\u2660', '\u2665', '\u2663'];
  if (trumpSuit === '\u2660') return ['\u2660', '\u2665', '\u2663', '\u2666'];
  if (trumpSuit === '\u2663') return ['\u2663', '\u2665', '\u2660', '\u2666'];
  return ['\u2660', '\u2665', '\u2663', '\u2666'];
};

/**
 * Sort cards within a suit by rank (high to low)
 */
export const sortCards = (cards) => {
  return [...cards].sort((a, b) => {
    const aRank = a.rank || a.r;
    const bRank = b.rank || b.r;
    return RANK_ORDER.indexOf(aRank) - RANK_ORDER.indexOf(bRank);
  });
};

/**
 * Normalize suit to Unicode format
 */
export const normalizeSuit = (suit) => {
  const map = { 'S': '\u2660', 'H': '\u2665', 'D': '\u2666', 'C': '\u2663' };
  return map[suit] || suit;
};

/**
 * Check if a suit is red (hearts/diamonds)
 */
export const isRedSuit = (suit) => {
  const normalized = normalizeSuit(suit);
  return normalized === '\u2665' || normalized === '\u2666';
};

/**
 * Extract trump strain from contract string (e.g., "4\u2660" -> "S", "3NT" -> "NT")
 */
export const extractTrumpStrain = (contract) => {
  if (!contract) return 'NT';
  const match = contract.match(/\d([SHDC\u2660\u2665\u2666\u2663]|NT)/i);
  if (match) {
    const s = match[1].toUpperCase();
    if (s === 'NT') return 'NT';
    const strainMap = {
      'S': 'S', '\u2660': 'S',
      'H': 'H', '\u2665': 'H',
      'D': 'D', '\u2666': 'D',
      'C': 'C', '\u2663': 'C'
    };
    return strainMap[s] || 'NT';
  }
  return 'NT';
};

/**
 * Group cards by suit and sort each group
 */
export const groupCardsBySuit = (cards) => {
  const grouped = { '\u2660': [], '\u2665': [], '\u2666': [], '\u2663': [] };
  cards.forEach(card => {
    const suit = normalizeSuit(card.suit || card.s);
    if (grouped[suit]) {
      grouped[suit].push({
        rank: card.rank || card.r,
        suit: suit
      });
    }
  });
  // Sort each suit
  Object.keys(grouped).forEach(suit => {
    grouped[suit] = sortCards(grouped[suit]);
  });
  return grouped;
};
