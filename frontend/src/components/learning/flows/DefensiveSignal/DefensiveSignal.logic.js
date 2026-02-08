/**
 * Defensive Signal Quiz - Logic Module
 * Handles evaluation of player's signal card selection
 */

import { RANK_ORDER } from '../../types/hand-types';

/**
 * Signal type descriptions
 */
export const SIGNAL_TYPE_INFO = {
  attitude: {
    name: 'Attitude',
    level: 1,
    description: 'High = encourage, Low = discourage',
    longDescription:
      'Attitude signals tell partner whether you want the suit continued. Play a high card to encourage (you have an honor or want the suit led), play a low card to discourage.',
  },
  count: {
    name: 'Count',
    level: 2,
    description: 'High-low = even, Low-high = odd',
    longDescription:
      'Count signals tell partner how many cards you hold in the suit. Start with a high card if you have an even number (2, 4, 6), start with a low card if you have an odd number (1, 3, 5).',
  },
  suitPreference: {
    name: 'Suit Preference',
    level: 3,
    description: 'High = higher suit, Low = lower suit',
    longDescription:
      'Suit preference signals tell partner which suit to return after winning the current trick. A high card asks for the higher-ranking of the two logical suits, a low card asks for the lower-ranking suit.',
  },
};

/**
 * Get the rank value for comparison (A=14, K=13, ..., 2=2)
 * @param {string} rank
 * @returns {number}
 */
export const getRankValue = (rank) => {
  const index = RANK_ORDER.indexOf(rank);
  if (index === -1) return 0;
  return 14 - index; // A=14, K=13, Q=12, etc.
};

/**
 * Get cards from a hand that belong to a specific suit
 * @param {Array<{rank: string, suit: string}>} hand
 * @param {string} suit
 * @returns {Array<{rank: string, suit: string}>}
 */
export const getCardsInSuit = (hand, suit) => {
  return hand
    .filter((card) => card.suit === suit)
    .sort((a, b) => getRankValue(b.rank) - getRankValue(a.rank));
};

/**
 * Determine if a card is the highest/lowest in the suit
 * @param {string} cardRank
 * @param {Array<{rank: string, suit: string}>} suitCards
 * @returns {{ isHighest: boolean, isLowest: boolean, position: number }}
 */
export const getCardPosition = (cardRank, suitCards) => {
  const sorted = [...suitCards].sort(
    (a, b) => getRankValue(b.rank) - getRankValue(a.rank)
  );
  const position = sorted.findIndex((c) => c.rank === cardRank);

  return {
    isHighest: position === 0,
    isLowest: position === sorted.length - 1,
    position: position,
    total: sorted.length,
  };
};

/**
 * Evaluate a player's signal card selection
 * @param {Object} situation - The signal situation from mockData
 * @param {string} selectedRank - The rank the player selected
 * @returns {Object} Evaluation result
 */
export const evaluateSignal = (situation, selectedRank) => {
  const { signalType, signalSuit, yourHand, correctCard } = situation;
  const suitCards = getCardsInSuit(yourHand, signalSuit);
  const position = getCardPosition(selectedRank, suitCards);
  const correctPosition = getCardPosition(correctCard, suitCards);

  const isExactlyCorrect = selectedRank === correctCard;

  // For signals, we can be somewhat lenient
  // High signal: top 2 cards are acceptable
  // Low signal: bottom 2 cards are acceptable
  let isAcceptable = false;
  let rating = 'incorrect';

  if (isExactlyCorrect) {
    isAcceptable = true;
    rating = 'optimal';
  } else if (signalType === 'attitude' || signalType === 'suitPreference') {
    // For attitude/suit preference, check if player got the direction right
    const wantedHigh = correctPosition.isHighest || correctPosition.position <= 1;
    const playedHigh = position.isHighest || position.position <= 1;
    const wantedLow = correctPosition.isLowest || correctPosition.position >= suitCards.length - 2;
    const playedLow = position.isLowest || position.position >= suitCards.length - 2;

    if (wantedHigh && playedHigh) {
      isAcceptable = true;
      rating = 'acceptable';
    } else if (wantedLow && playedLow) {
      isAcceptable = true;
      rating = 'acceptable';
    }
  } else if (signalType === 'count') {
    // For count, must get the high/low direction correct
    const wantedHigh = correctPosition.position <= 1;
    const playedHigh = position.position <= 1;
    const wantedLow = correctPosition.position >= suitCards.length - 2;
    const playedLow = position.position >= suitCards.length - 2;

    if (wantedHigh && playedHigh) {
      isAcceptable = true;
      rating = 'acceptable';
    } else if (wantedLow && playedLow) {
      isAcceptable = true;
      rating = 'acceptable';
    }
  }

  return {
    isCorrect: isExactlyCorrect || isAcceptable,
    isExactlyCorrect,
    isAcceptable,
    rating,
    selectedRank,
    correctCard,
    explanation: situation.explanation,
    signalType,
    signalTypeInfo: SIGNAL_TYPE_INFO[signalType],
  };
};

/**
 * Get the indices of cards that should be disabled (not in signal suit)
 * @param {Array<{rank: string, suit: string}>} hand - Full hand
 * @param {string} signalSuit - The suit to signal in
 * @returns {number[]} Indices of cards to disable
 */
export const getDisabledIndices = (hand, signalSuit) => {
  const indices = [];
  hand.forEach((card, index) => {
    if (card.suit !== signalSuit) {
      indices.push(index);
    }
  });
  return indices;
};

/**
 * Calculate session summary statistics
 * @param {Array<{situation: Object, selectedRank: string, result: Object}>} decisions
 * @returns {Object} Summary statistics
 */
export const calculateSummary = (decisions) => {
  const total = decisions.length;
  const correct = decisions.filter((d) => d.result.isCorrect).length;

  const byType = {
    attitude: { correct: 0, total: 0 },
    count: { correct: 0, total: 0 },
    suitPreference: { correct: 0, total: 0 },
  };

  decisions.forEach((d) => {
    const type = d.situation.signalType;
    byType[type].total += 1;
    if (d.result.isCorrect) {
      byType[type].correct += 1;
    }
  });

  const getAccuracy = (stats) => {
    if (stats.total === 0) return null;
    return Math.round((stats.correct / stats.total) * 100);
  };

  return {
    totalCorrect: correct,
    totalQuestions: total,
    overallScore: Math.round((correct / total) * 100),
    byType: {
      attitude: {
        ...byType.attitude,
        accuracy: getAccuracy(byType.attitude),
      },
      count: {
        ...byType.count,
        accuracy: getAccuracy(byType.count),
      },
      suitPreference: {
        ...byType.suitPreference,
        accuracy: getAccuracy(byType.suitPreference),
      },
    },
  };
};

/**
 * Build FlowResult for analytics
 * @param {Array<{situation: Object, selectedRank: string, result: Object}>} decisions
 * @returns {Object} FlowResult
 */
export const buildFlowResult = (decisions) => {
  const summary = calculateSummary(decisions);

  return {
    flowType: 'signal',
    handId: `signal_session_${Date.now()}`,
    timestamp: new Date().toISOString(),
    decisions: decisions.map((d, index) => ({
      decisionId: `signal_${d.situation.id}`,
      category: `signal_${d.situation.signalType}`,
      playerAnswer: d.selectedRank,
      correctAnswer: d.situation.correctCard,
      isCorrect: d.result.isCorrect,
      explanation: d.situation.explanation,
      conventionTag: d.situation.signalType,
    })),
    overallScore: summary.overallScore,
    timeSpent: 0, // Could track this if needed
    conventionTags: ['attitude', 'count', 'suitPreference'],
  };
};

/**
 * Defensive Signal logic module exports
 */
const DefensiveSignalLogic = {
  SIGNAL_TYPE_INFO,
  evaluateSignal,
  getCardsInSuit,
  getDisabledIndices,
  calculateSummary,
  buildFlowResult,
};

export default DefensiveSignalLogic;
