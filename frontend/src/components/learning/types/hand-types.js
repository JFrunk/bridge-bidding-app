/**
 * Hand and Card Type Definitions for Learning Flows
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 *
 * These are JSDoc type definitions for use with JavaScript components.
 */

/**
 * @typedef {'S' | 'H' | 'D' | 'C'} Suit
 * Suit abbreviations: S=Spades, H=Hearts, D=Diamonds, C=Clubs
 */

/**
 * @typedef {'A' | 'K' | 'Q' | 'J' | '10' | '9' | '8' | '7' | '6' | '5' | '4' | '3' | '2'} Rank
 */

/**
 * @typedef {Object} Card
 * @property {Rank} rank - The card rank (A, K, Q, J, 10-2)
 * @property {Suit} suit - The card suit (S, H, D, C)
 */

/**
 * @typedef {Card[]} Hand
 * A hand is an array of 13 cards
 */

/**
 * @typedef {Object} FourHands
 * @property {Hand} north
 * @property {Hand} east
 * @property {Hand} south
 * @property {Hand} west
 */

/**
 * @typedef {Object} Bid
 * @property {string} bid - The bid string (e.g., "1H", "3NT", "Pass", "X", "XX")
 * @property {'N' | 'E' | 'S' | 'W'} bidder - Who made the bid
 * @property {string} [explanation] - Optional explanation of the bid
 */

/**
 * @typedef {Object} Contract
 * @property {number} level - Contract level (1-7)
 * @property {'S' | 'H' | 'D' | 'C' | 'NT'} strain - Trump suit or NT
 * @property {'N' | 'E' | 'S' | 'W'} declarer - Who plays the contract
 * @property {boolean} doubled - Whether the contract is doubled
 * @property {boolean} redoubled - Whether the contract is redoubled
 */

/**
 * @typedef {Object} TrickPlay
 * @property {number} trickNumber - Which trick (1-13)
 * @property {Card[]} cards - Cards played in order (leader first)
 * @property {'N' | 'E' | 'S' | 'W'} leader - Who led to the trick
 * @property {'N' | 'E' | 'S' | 'W'} winner - Who won the trick
 */

/**
 * @typedef {Object} DDSResult
 * @property {number} tricks - Maximum tricks makeable
 * @property {Object.<string, number>} byStrain - Tricks by each strain
 */

// Suit display helpers
export const SUIT_SYMBOLS = {
  S: '♠',
  H: '♥',
  D: '♦',
  C: '♣',
};

export const SUIT_NAMES = {
  S: 'spades',
  H: 'hearts',
  D: 'diamonds',
  C: 'clubs',
};

export const SUIT_ORDER = ['S', 'H', 'C', 'D']; // Display order: ♠♥♣♦

export const RANK_ORDER = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];

/**
 * Check if a suit is red (hearts or diamonds)
 * @param {Suit} suit
 * @returns {boolean}
 */
export const isRedSuit = (suit) => suit === 'H' || suit === 'D';

/**
 * Sort cards by suit (♠♥♣♦) then by rank (high to low)
 * @param {Card[]} cards
 * @returns {Card[]}
 */
export const sortCards = (cards) => {
  return [...cards].sort((a, b) => {
    const suitDiff = SUIT_ORDER.indexOf(a.suit) - SUIT_ORDER.indexOf(b.suit);
    if (suitDiff !== 0) return suitDiff;
    return RANK_ORDER.indexOf(a.rank) - RANK_ORDER.indexOf(b.rank);
  });
};

/**
 * Group cards by suit
 * @param {Card[]} cards
 * @returns {Object.<Suit, Card[]>}
 */
export const groupBySuit = (cards) => {
  const groups = { S: [], H: [], C: [], D: [] };
  for (const card of cards) {
    groups[card.suit].push(card);
  }
  // Sort each suit by rank
  for (const suit of SUIT_ORDER) {
    groups[suit].sort((a, b) => RANK_ORDER.indexOf(a.rank) - RANK_ORDER.indexOf(b.rank));
  }
  return groups;
};
