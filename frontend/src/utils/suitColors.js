/**
 * Suit & Bid Utilities
 *
 * Single source of truth for suit symbols, colors, and bid formatting.
 * Import from here instead of defining inline maps.
 *
 * Uses design token colors from tailwind.config.js:
 * - suit-red (#d32f2f) = --card-red
 * - suit-black (#1a1a1a) = --card-black
 */

// === CONSTANTS ===

/** Letter to Unicode symbol mapping */
export const SUIT_MAP = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };

/** Unicode symbol to letter mapping (reverse of SUIT_MAP) */
export const SYMBOL_TO_LETTER = { '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C' };

/** Bidirectional suit lookup (accepts both formats) */
export const SUIT_LOOKUP = {
  'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣',
  '♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣'
};

/** Suit names for display and accessibility (aria-labels) */
export const SUIT_NAMES = {
  '♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs',
  'S': 'spades', 'H': 'hearts', 'D': 'diamonds', 'C': 'clubs'
};

/** Red suits set — accepts both letter and symbol formats */
const RED_SUITS = new Set(['H', 'D', '♥', '♦', 'Hearts', 'Diamonds']);


// === FUNCTIONS ===

/**
 * Check if a suit is red (hearts or diamonds).
 * @param {string} suit - Suit letter, symbol, or name ('H', '♥', 'Hearts', etc.)
 * @returns {boolean}
 */
export function isRedSuit(suit) {
  return RED_SUITS.has(suit);
}

/**
 * Get the Tailwind color class for a suit symbol.
 * @param {string} suit - Suit symbol or name ('H', 'D', '♥', '♦', 'Hearts', 'Diamonds', etc.)
 * @param {boolean} onDarkBackground - If true, use lighter colors for dark green table
 * @returns {string} Tailwind color class
 */
export function getSuitColorClass(suit, onDarkBackground = false) {
  if (onDarkBackground) {
    return isRedSuit(suit) ? 'text-red-300' : 'text-white';
  }
  return isRedSuit(suit) ? 'text-suit-red' : 'text-suit-black';
}

/**
 * Normalize a suit to its Unicode symbol.
 * @param {string} suit - Suit in any format ('S', '♠', 'spades', etc.)
 * @returns {string} Unicode symbol ('♠', '♥', '♦', '♣')
 */
export function normalizeSuit(suit) {
  if (!suit) return suit;
  if (SUIT_LOOKUP[suit]) return SUIT_LOOKUP[suit];
  // Handle full names
  const nameMap = { 'SPADES': '♠', 'HEARTS': '♥', 'DIAMONDS': '♦', 'CLUBS': '♣' };
  return nameMap[suit.toUpperCase()] || suit;
}

/**
 * Extract suit from a bid string (e.g., "2H" -> "H", "3NT" -> "NT").
 * @param {string} bid - Bid string like "1S", "2H", "3NT", "Pass", "X"
 * @returns {string} Suit portion of bid
 */
export function extractSuitFromBid(bid) {
  if (!bid || typeof bid !== 'string') return '';
  const suitPart = bid.replace(/[0-9]/g, '').trim();
  return suitPart;
}

/**
 * Extract level from a bid string (e.g., "2H" -> 2, "3NT" -> 3).
 * @param {string} bid - Bid string like "1S", "2H", "3NT"
 * @returns {number|null} Bid level (1-7) or null if not a level bid
 */
export function extractLevelFromBid(bid) {
  if (!bid || typeof bid !== 'string') return null;
  const match = bid.match(/^([1-7])/);
  return match ? parseInt(match[1], 10) : null;
}

/**
 * Check if a bid is a special bid (Pass, Double, Redouble).
 * @param {string} bid - Bid string
 * @returns {boolean}
 */
export function isSpecialBid(bid) {
  if (!bid) return false;
  const specialBids = ['Pass', 'DBL', 'RDBL', 'X', 'XX', 'Dbl', 'Rdbl', 'PASS'];
  return specialBids.includes(bid);
}

/**
 * Format a bid for display with proper suit symbols.
 * @param {string} bid - Bid string like "1S", "2H"
 * @returns {string} Formatted bid like "1♠", "2♥"
 */
export function formatBidDisplay(bid) {
  if (!bid) return '';

  let formatted = bid;
  Object.entries(SUIT_MAP).forEach(([letter, symbol]) => {
    formatted = formatted.replace(new RegExp(letter + '(?![a-z])', 'g'), symbol);
  });

  return formatted;
}
