/**
 * Suit Color Utilities
 * Per UI_UX_CONSTITUTION.md:
 * - Hearts (♥) and Diamonds (♦) = text-red-600
 * - Spades (♠), Clubs (♣), and NT = text-gray-900
 */

/**
 * Get the Tailwind color class for a suit symbol
 * @param {string} suit - Suit symbol or name ('H', 'D', '♥', '♦', 'Hearts', 'Diamonds', etc.)
 * @param {boolean} onDarkBackground - If true, use lighter colors for dark green table
 * @returns {string} Tailwind color class
 */
export function getSuitColorClass(suit, onDarkBackground = false) {
  const redSuits = ['H', 'D', '♥', '♦', 'Hearts', 'Diamonds'];
  const isRedSuit = redSuits.includes(suit);

  if (onDarkBackground) {
    // On green table: lighter colors for visibility
    return isRedSuit ? 'text-red-300' : 'text-white';
  }

  // On white/beige surfaces: standard high contrast
  return isRedSuit ? 'text-red-600' : 'text-gray-900';
}

/**
 * Extract suit from a bid string (e.g., "2H" -> "H", "3NT" -> "NT")
 * @param {string} bid - Bid string like "1S", "2H", "3NT", "Pass", "X"
 * @returns {string} Suit portion of bid
 */
export function extractSuitFromBid(bid) {
  if (!bid || typeof bid !== 'string') return '';

  // Remove level number
  const suitPart = bid.replace(/[0-9]/g, '').trim();
  return suitPart;
}

/**
 * Check if a bid is a special bid (Pass, Double, Redouble)
 * @param {string} bid - Bid string
 * @returns {boolean}
 */
export function isSpecialBid(bid) {
  if (!bid) return false;
  const specialBids = ['Pass', 'DBL', 'RDBL', 'X', 'XX', 'Dbl', 'Rdbl', 'PASS'];
  return specialBids.includes(bid);
}

/**
 * Format a bid for display with proper suit symbols
 * @param {string} bid - Bid string like "1S", "2H"
 * @returns {string} Formatted bid like "1♠", "2♥"
 */
export function formatBidDisplay(bid) {
  if (!bid) return '';

  const suitMap = {
    'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣',
    '♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣'
  };

  // Replace suit letters with symbols
  let formatted = bid;
  Object.entries(suitMap).forEach(([letter, symbol]) => {
    if (letter.length === 1 && letter === letter.toUpperCase()) {
      formatted = formatted.replace(new RegExp(letter + '(?![a-z])', 'g'), symbol);
    }
  });

  return formatted;
}

export default {
  getSuitColorClass,
  extractSuitFromBid,
  isSpecialBid,
  formatBidDisplay
};
