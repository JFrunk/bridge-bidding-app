/**
 * QuickCount.logic.js
 *
 * Hand generation, point calculation, and timer logic for the Quick Count drill.
 * All hand generation and counting happens client-side.
 */

import { SUIT_ORDER, RANK_ORDER, SUIT_SYMBOLS, groupBySuit } from '../../types/hand-types';

// ============================================================================
// Constants
// ============================================================================

export const LEVELS = {
  HCP_ONLY: 1,
  HCP_PLUS_LENGTH: 2,
  HCP_PLUS_SHORTNESS: 3,
  DECLARER_VS_DUMMY: 4
};

export const LEVEL_NAMES = {
  [LEVELS.HCP_ONLY]: 'HCP Only',
  [LEVELS.HCP_PLUS_LENGTH]: 'HCP + Length',
  [LEVELS.HCP_PLUS_SHORTNESS]: 'HCP + Shortness (Dummy)',
  [LEVELS.DECLARER_VS_DUMMY]: 'Declarer vs Dummy'
};

export const LEVEL_DESCRIPTIONS = {
  [LEVELS.HCP_ONLY]: 'A=4, K=3, Q=2, J=1',
  [LEVELS.HCP_PLUS_LENGTH]: 'HCP + 1 per card over 4 in any suit',
  [LEVELS.HCP_PLUS_SHORTNESS]: 'HCP + void=5, singleton=3, doubleton=1',
  [LEVELS.DECLARER_VS_DUMMY]: 'Choose length or shortness based on role'
};

export const HANDS_PER_ROUND = 10;

// HCP values by rank
const HCP_VALUES = {
  'A': 4,
  'K': 3,
  'Q': 2,
  'J': 1
};

// Shortness points (for dummy)
const SHORTNESS_POINTS = {
  0: 5,  // void
  1: 3,  // singleton
  2: 1   // doubleton
};

// Trump suits for Level 4
const TRUMP_SUITS = ['S', 'H', 'D', 'C'];

// ============================================================================
// Deck Creation and Shuffling
// ============================================================================

/**
 * Create a standard 52-card deck
 * @returns {Array<{rank: string, suit: string}>}
 */
export function createDeck() {
  const deck = [];
  for (const suit of SUIT_ORDER) {
    for (const rank of RANK_ORDER) {
      deck.push({ rank, suit });
    }
  }
  return deck;
}

/**
 * Fisher-Yates shuffle
 * @param {Array} array
 * @returns {Array}
 */
export function shuffle(array) {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

/**
 * Sort cards by suit (S, H, C, D) then by rank (high to low)
 * @param {Array<{rank: string, suit: string}>} cards
 * @returns {Array<{rank: string, suit: string}>}
 */
export function sortBySuitThenRank(cards) {
  return [...cards].sort((a, b) => {
    const suitDiff = SUIT_ORDER.indexOf(a.suit) - SUIT_ORDER.indexOf(b.suit);
    if (suitDiff !== 0) return suitDiff;
    return RANK_ORDER.indexOf(a.rank) - RANK_ORDER.indexOf(b.rank);
  });
}

/**
 * Generate a random 13-card bridge hand
 * @returns {Array<{rank: string, suit: string}>}
 */
export function generateRandomHand() {
  const deck = createDeck();
  const shuffled = shuffle(deck);
  return sortBySuitThenRank(shuffled.slice(0, 13));
}

// ============================================================================
// Point Calculation
// ============================================================================

/**
 * Calculate High Card Points for a hand
 * @param {Array<{rank: string, suit: string}>} hand
 * @returns {number}
 */
export function calculateHCP(hand) {
  return hand.reduce((total, card) => {
    return total + (HCP_VALUES[card.rank] || 0);
  }, 0);
}

/**
 * Calculate length points (1 for each card over 4 in any suit)
 * @param {Array<{rank: string, suit: string}>} hand
 * @returns {number}
 */
export function calculateLengthPoints(hand) {
  const groups = groupBySuit(hand);
  let lengthPoints = 0;

  for (const suit of SUIT_ORDER) {
    const suitLength = groups[suit].length;
    if (suitLength > 4) {
      lengthPoints += suitLength - 4;
    }
  }

  return lengthPoints;
}

/**
 * Calculate shortness points for dummy (void=5, singleton=3, doubleton=1)
 * @param {Array<{rank: string, suit: string}>} hand
 * @param {string} [trumpSuit] - Optional trump suit to exclude from shortness
 * @returns {number}
 */
export function calculateShortnessPoints(hand, trumpSuit = null) {
  const groups = groupBySuit(hand);
  let shortnessPoints = 0;

  for (const suit of SUIT_ORDER) {
    // Skip trump suit for shortness points
    if (trumpSuit && suit === trumpSuit) continue;

    const suitLength = groups[suit].length;
    if (suitLength in SHORTNESS_POINTS) {
      shortnessPoints += SHORTNESS_POINTS[suitLength];
    }
  }

  return shortnessPoints;
}

/**
 * Get suit lengths for a hand
 * @param {Array<{rank: string, suit: string}>} hand
 * @returns {Object.<string, number>}
 */
export function getSuitLengths(hand) {
  const groups = groupBySuit(hand);
  const lengths = {};
  for (const suit of SUIT_ORDER) {
    lengths[suit] = groups[suit].length;
  }
  return lengths;
}

/**
 * Calculate total points based on level
 * @param {Array<{rank: string, suit: string}>} hand
 * @param {number} level - LEVELS constant
 * @param {Object} options - Additional options for Level 4
 * @param {string} options.trumpSuit - Trump suit for Level 4
 * @param {boolean} options.isDummy - Whether counting as dummy (Level 4)
 * @returns {number}
 */
export function calculateTotalPoints(hand, level, options = {}) {
  const hcp = calculateHCP(hand);

  switch (level) {
    case LEVELS.HCP_ONLY:
      return hcp;

    case LEVELS.HCP_PLUS_LENGTH:
      return hcp + calculateLengthPoints(hand);

    case LEVELS.HCP_PLUS_SHORTNESS:
      return hcp + calculateShortnessPoints(hand);

    case LEVELS.DECLARER_VS_DUMMY: {
      const { trumpSuit, isDummy } = options;
      if (isDummy) {
        // Dummy uses shortness points (excluding trump)
        return hcp + calculateShortnessPoints(hand, trumpSuit);
      } else {
        // Declarer uses length points
        return hcp + calculateLengthPoints(hand);
      }
    }

    default:
      return hcp;
  }
}

// ============================================================================
// Point Breakdown for Display
// ============================================================================

/**
 * Generate a breakdown string showing how points were calculated
 * @param {Array<{rank: string, suit: string}>} hand
 * @param {number} level
 * @param {Object} options - Additional options for Level 4
 * @returns {string}
 */
export function getPointBreakdown(hand, level, options = {}) {
  const groups = groupBySuit(hand);
  const hcp = calculateHCP(hand);

  // Build HCP breakdown
  const hcpParts = [];
  for (const suit of SUIT_ORDER) {
    for (const card of groups[suit]) {
      if (HCP_VALUES[card.rank]) {
        hcpParts.push(`${card.rank}(${HCP_VALUES[card.rank]})`);
      }
    }
  }

  const hcpBreakdown = hcpParts.length > 0
    ? hcpParts.join(' + ')
    : 'No honors';

  switch (level) {
    case LEVELS.HCP_ONLY:
      return `${hcpBreakdown} = ${hcp} HCP`;

    case LEVELS.HCP_PLUS_LENGTH: {
      const lengthPoints = calculateLengthPoints(hand);
      const lengthParts = [];
      for (const suit of SUIT_ORDER) {
        const len = groups[suit].length;
        if (len > 4) {
          lengthParts.push(`${SUIT_SYMBOLS[suit]}+${len - 4}`);
        }
      }
      const lengthBreakdown = lengthParts.length > 0
        ? lengthParts.join(', ')
        : 'no length';

      return `${hcpBreakdown} = ${hcp} HCP + ${lengthBreakdown} = ${hcp + lengthPoints} total`;
    }

    case LEVELS.HCP_PLUS_SHORTNESS: {
      const shortPoints = calculateShortnessPoints(hand);
      const shortParts = [];
      for (const suit of SUIT_ORDER) {
        const len = groups[suit].length;
        if (len === 0) {
          shortParts.push(`${SUIT_SYMBOLS[suit]} void(+5)`);
        } else if (len === 1) {
          shortParts.push(`${SUIT_SYMBOLS[suit]} singleton(+3)`);
        } else if (len === 2) {
          shortParts.push(`${SUIT_SYMBOLS[suit]} doubleton(+1)`);
        }
      }
      const shortBreakdown = shortParts.length > 0
        ? shortParts.join(', ')
        : 'no shortness';

      return `${hcpBreakdown} = ${hcp} HCP + ${shortBreakdown} = ${hcp + shortPoints} total`;
    }

    case LEVELS.DECLARER_VS_DUMMY: {
      const { trumpSuit, isDummy } = options;
      const trumpSymbol = SUIT_SYMBOLS[trumpSuit];

      if (isDummy) {
        const shortPoints = calculateShortnessPoints(hand, trumpSuit);
        const shortParts = [];
        for (const suit of SUIT_ORDER) {
          if (suit === trumpSuit) continue;
          const len = groups[suit].length;
          if (len === 0) {
            shortParts.push(`${SUIT_SYMBOLS[suit]} void(+5)`);
          } else if (len === 1) {
            shortParts.push(`${SUIT_SYMBOLS[suit]} singleton(+3)`);
          } else if (len === 2) {
            shortParts.push(`${SUIT_SYMBOLS[suit]} doubleton(+1)`);
          }
        }
        const shortBreakdown = shortParts.length > 0
          ? shortParts.join(', ')
          : 'no shortness';

        return `Dummy (${trumpSymbol} trump): ${hcpBreakdown} = ${hcp} HCP + ${shortBreakdown} = ${hcp + shortPoints} total`;
      } else {
        const lengthPoints = calculateLengthPoints(hand);
        const lengthParts = [];
        for (const suit of SUIT_ORDER) {
          const len = groups[suit].length;
          if (len > 4) {
            lengthParts.push(`${SUIT_SYMBOLS[suit]}+${len - 4}`);
          }
        }
        const lengthBreakdown = lengthParts.length > 0
          ? lengthParts.join(', ')
          : 'no length';

        return `Declarer (${trumpSymbol} trump): ${hcpBreakdown} = ${hcp} HCP + ${lengthBreakdown} = ${hcp + lengthPoints} total`;
      }
    }

    default:
      return `${hcpBreakdown} = ${hcp} HCP`;
  }
}

// ============================================================================
// Choice Generation
// ============================================================================

/**
 * Generate 6 choices centered around the correct answer
 * Choices are: correct-2, correct-1, correct, correct+1, correct+2, correct+3
 * Shuffled to prevent patterns
 * @param {number} correctAnswer
 * @returns {Array<{id: string, label: string, value: number}>}
 */
export function generateChoices(correctAnswer) {
  // Generate offsets: -2, -1, 0, +1, +2, +3
  const offsets = [-2, -1, 0, 1, 2, 3];

  const choices = offsets.map(offset => {
    const value = Math.max(0, correctAnswer + offset); // Don't go below 0
    return {
      id: `choice-${value}`,
      label: `${value}`,
      value
    };
  });

  // Remove duplicates (can happen if correctAnswer is 0 or 1)
  const uniqueChoices = [];
  const seenValues = new Set();
  for (const choice of choices) {
    if (!seenValues.has(choice.value)) {
      seenValues.add(choice.value);
      uniqueChoices.push(choice);
    }
  }

  // If we removed duplicates, add more choices above
  let nextValue = correctAnswer + 4;
  while (uniqueChoices.length < 6) {
    if (!seenValues.has(nextValue)) {
      uniqueChoices.push({
        id: `choice-${nextValue}`,
        label: `${nextValue}`,
        value: nextValue
      });
      seenValues.add(nextValue);
    }
    nextValue++;
  }

  // Shuffle the choices
  return shuffle(uniqueChoices);
}

// ============================================================================
// Level 4: Trump Suit Generation
// ============================================================================

/**
 * Generate a random trump suit for Level 4
 * @returns {string}
 */
export function getRandomTrumpSuit() {
  return TRUMP_SUITS[Math.floor(Math.random() * TRUMP_SUITS.length)];
}

/**
 * Determine if counting as dummy or declarer for Level 4
 * Alternates or random
 * @param {number} handIndex - Index within the round
 * @returns {boolean} - true if dummy, false if declarer
 */
export function shouldCountAsDummy(handIndex) {
  // Alternate between declarer and dummy
  return handIndex % 2 === 1;
}

// ============================================================================
// Timer Utilities
// ============================================================================

/**
 * Format time in seconds to display format
 * @param {number} seconds
 * @returns {string}
 */
export function formatTime(seconds) {
  return seconds.toFixed(1);
}

/**
 * Calculate average time from an array of times
 * @param {number[]} times - Array of times in seconds
 * @returns {number}
 */
export function calculateAverageTime(times) {
  if (times.length === 0) return 0;
  return times.reduce((sum, t) => sum + t, 0) / times.length;
}

// ============================================================================
// Round and Score Utilities
// ============================================================================

/**
 * Generate a hand data object for a round
 * @param {number} level
 * @param {number} handIndex
 * @returns {Object}
 */
export function generateHandData(level, handIndex) {
  const hand = generateRandomHand();

  let options = {};
  let prompt = '';

  if (level === LEVELS.DECLARER_VS_DUMMY) {
    const trumpSuit = getRandomTrumpSuit();
    const isDummy = shouldCountAsDummy(handIndex);
    options = { trumpSuit, isDummy };

    const trumpSymbol = SUIT_SYMBOLS[trumpSuit];
    const role = isDummy ? 'DUMMY' : 'DECLARER';
    prompt = `You are ${role}. Trump is ${trumpSymbol}. How many points?`;
  } else {
    prompt = 'How many points?';
  }

  const correctAnswer = calculateTotalPoints(hand, level, options);
  const choices = generateChoices(correctAnswer);

  return {
    hand,
    level,
    options,
    prompt,
    correctAnswer,
    choices,
    handIndex
  };
}

/**
 * Calculate score percentage for a round
 * @param {number} correct
 * @param {number} total
 * @returns {number} - 0-100
 */
export function calculateScorePercentage(correct, total) {
  if (total === 0) return 0;
  return Math.round((correct / total) * 100);
}

/**
 * Get performance rating based on accuracy
 * @param {number} percentage - 0-100
 * @returns {'good' | 'neutral' | 'bad'}
 */
export function getPerformanceRating(percentage) {
  if (percentage >= 80) return 'good';
  if (percentage >= 60) return 'neutral';
  return 'bad';
}
