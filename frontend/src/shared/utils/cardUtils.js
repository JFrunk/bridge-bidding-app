/**
 * Card Utilities
 *
 * Single source of truth for card manipulation, sorting, grouping, and display.
 * Import from here instead of defining inline rank/suit logic.
 *
 * For suit symbols, colors, and bid formatting, use utils/suitColors.js instead.
 */

import { SUIT_LOOKUP, isRedSuit } from '../../utils/suitColors';

// === CONSTANTS ===

/** Standard suit display order (no trump / default) */
export const SUIT_ORDER = ['♠', '♥', '♣', '♦'];

/** Rank ordering map — higher value = higher rank */
export const RANK_ORDER = { 'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2 };

/** Rank display map — converts internal rank to display string */
export const RANK_DISPLAY = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };


// === FUNCTIONS ===

/**
 * Get suit display order based on trump suit.
 * Trump on left, then highest opposite color suit descending.
 *
 * @param {string|null} trumpStrain - Trump suit ('♠', '♥', '♦', '♣', 'S', 'H', 'D', 'C', 'NT', or null)
 * @returns {string[]} Array of suit symbols in display order
 */
export function getSuitOrder(trumpStrain) {
  if (!trumpStrain || trumpStrain === 'NT') {
    return ['♠', '♥', '♣', '♦'];
  }

  const trumpSuit = SUIT_LOOKUP[trumpStrain] || trumpStrain;

  if (trumpSuit === '♥') return ['♥', '♠', '♦', '♣'];
  if (trumpSuit === '♦') return ['♦', '♠', '♥', '♣'];
  if (trumpSuit === '♠') return ['♠', '♥', '♣', '♦'];
  if (trumpSuit === '♣') return ['♣', '♥', '♠', '♦'];

  return ['♠', '♥', '♣', '♦'];
}

/**
 * Sort cards by rank (descending). Handles both {rank, suit} and {r, s} formats.
 *
 * @param {Array} cards - Array of card objects with rank (or r) property
 * @returns {Array} New sorted array (does not mutate input)
 */
export function sortCards(cards) {
  return [...cards].sort((a, b) => {
    const rankA = RANK_ORDER[a.rank || a.r] || 0;
    const rankB = RANK_ORDER[b.rank || b.r] || 0;
    return rankB - rankA;
  });
}

/**
 * Group cards by suit.
 *
 * @param {Array} cards - Array of card objects with suit property
 * @returns {Object} Object with suit symbols as keys and card arrays as values
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
 * Convert rank character to display string ('T' -> '10').
 *
 * @param {string} rank - Card rank ('A', 'K', 'Q', 'J', 'T', '9', etc.)
 * @returns {string} Display string ('A', 'K', 'Q', 'J', '10', '9', etc.)
 */
export function rankToDisplay(rank) {
  return RANK_DISPLAY[rank] || rank;
}

/**
 * Get suit color CSS class.
 * For Tailwind classes, use getSuitColorClass() from utils/suitColors instead.
 *
 * @param {string} suit - Suit symbol ('♥', '♦', '♠', '♣') or letter ('H', 'D', 'S', 'C')
 * @returns {string} CSS class name ('suit-red' or 'suit-black')
 */
export function getSuitColor(suit) {
  return isRedSuit(suit) ? 'suit-red' : 'suit-black';
}

/**
 * Parse contract string.
 *
 * @param {string} contractStr - Contract string (e.g., "3NT", "4♠", "6♥X")
 * @returns {Object|null} Parsed contract { level, strain, doubled } or null
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
 * Format contract for display.
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
