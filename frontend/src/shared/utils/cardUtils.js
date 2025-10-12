/**
 * Card Utilities
 *
 * Shared utility functions for card manipulation and display.
 * Used by both bidding and play modules.
 */

/**
 * Get suit display order based on trump suit
 * Trump on left, then highest opposite color suit descending
 * No Trump: S, H, C, D (standard bidding order)
 *
 * @param {string|null} trumpStrain - Trump suit ('♠', '♥', '♦', '♣', 'NT', or null)
 * @returns {string[]} Array of suits in display order
 */
export function getSuitOrder(trumpStrain) {
  // No trump case
  if (!trumpStrain || trumpStrain === 'NT') {
    return ['♠', '♥', '♣', '♦'];
  }

  const strainToSuit = {
    'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣',
    '♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣'
  };

  const trumpSuit = strainToSuit[trumpStrain] || trumpStrain;

  if (trumpSuit === '♥') {
    return ['♥', '♠', '♦', '♣']; // Red trump: Hearts, Spades, Diamonds, Clubs
  } else if (trumpSuit === '♦') {
    return ['♦', '♠', '♥', '♣']; // Red trump: Diamonds, Spades, Hearts, Clubs
  } else if (trumpSuit === '♠') {
    return ['♠', '♥', '♣', '♦']; // Black trump: Spades, Hearts, Clubs, Diamonds
  } else if (trumpSuit === '♣') {
    return ['♣', '♥', '♠', '♦']; // Black trump: Clubs, Hearts, Spades, Diamonds
  }

  // Default fallback
  return ['♠', '♥', '♣', '♦'];
}

/**
 * Sort cards within a suit by rank
 *
 * @param {Array} cards - Array of card objects
 * @returns {Array} Sorted array of cards
 */
export function sortCards(cards) {
  const rankOrder = { 'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2 };
  return [...cards].sort((a, b) => rankOrder[b.rank] - rankOrder[a.rank]);
}

/**
 * Group cards by suit
 *
 * @param {Array} cards - Array of card objects
 * @returns {Object} Object with suits as keys and card arrays as values
 */
export function groupCardsBySuit(cards) {
  const groups = { '♠': [], '♥': [], '♦': [], '♣': [] };
  cards.forEach(card => {
    if (groups[card.suit]) {
      groups[card.suit].push(card);
    }
  });
  return groups;
}

/**
 * Convert rank character to display string
 *
 * @param {string} rank - Card rank ('A', 'K', 'Q', 'J', 'T', '9', etc.)
 * @returns {string} Display string ('A', 'K', 'Q', 'J', '10', '9', etc.)
 */
export function rankToDisplay(rank) {
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  return rankMap[rank] || rank;
}

/**
 * Get suit color class
 *
 * @param {string} suit - Suit symbol
 * @returns {string} CSS class name ('suit-red' or 'suit-black')
 */
export function getSuitColor(suit) {
  return (suit === '♥' || suit === '♦') ? 'suit-red' : 'suit-black';
}

/**
 * Parse contract string
 *
 * @param {string} contractStr - Contract string (e.g., "3NT", "4♠", "6♥X")
 * @returns {Object} Parsed contract { level, strain, doubled }
 */
export function parseContract(contractStr) {
  if (!contractStr) return null;

  const match = contractStr.match(/^([1-7])(♠|♥|♦|♣|NT)(X{0,2})$/);
  if (!match) return null;

  return {
    level: parseInt(match[1], 10),
    strain: match[2],
    doubled: match[3].length
  };
}

/**
 * Format contract for display
 *
 * @param {Object} contract - Contract object { level, strain, doubled }
 * @returns {string} Formatted contract string
 */
export function formatContract(contract) {
  if (!contract) return '';
  const { level, strain, doubled } = contract;
  const doubleStr = doubled === 2 ? 'XX' : (doubled === 1 ? 'X' : '');
  return `${level}${strain}${doubleStr}`;
}
