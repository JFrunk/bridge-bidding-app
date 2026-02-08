/**
 * Mock Data for Bidding Replay Flow
 *
 * Sample review items for development and testing.
 * These represent hands where the user made incorrect bids.
 */

import { addDays, getToday } from './spacedRepetition';

/**
 * Sample review items for testing
 * Each represents a bidding decision the user got wrong
 */
export const MOCK_REVIEW_ITEMS = [
  {
    handId: 'hand_001',
    decisionPoint: 'response_to_1nt',
    conventionTag: 'stayman',
    category: 'responses',
    intervalIndex: 0,
    nextReviewDate: getToday(), // Due today
    attempts: 1,
    correctStreak: 0,
    lastCorrect: false,
    previousBid: '3NT',
    correctBid: '2C',
    handData: {
      hand: [
        { rank: 'K', suit: 'S' },
        { rank: 'Q', suit: 'S' },
        { rank: '10', suit: 'S' },
        { rank: '5', suit: 'S' },
        { rank: 'A', suit: 'H' },
        { rank: 'J', suit: 'H' },
        { rank: '7', suit: 'H' },
        { rank: '3', suit: 'H' },
        { rank: 'K', suit: 'D' },
        { rank: '8', suit: 'D' },
        { rank: 'Q', suit: 'C' },
        { rank: '6', suit: 'C' },
        { rank: '2', suit: 'C' }
      ],
      auction: [
        { bid: '1NT', bidder: 'N', explanation: 'Balanced 15-17 HCP' }
      ],
      dealer: 'N',
      vulnerability: 'None',
      hcp: 14
    },
    createdAt: addDays(getToday(), -2)
  },
  {
    handId: 'hand_002',
    decisionPoint: 'jacoby_transfer',
    conventionTag: 'jacoby',
    category: 'responses',
    intervalIndex: 1,
    nextReviewDate: getToday(), // Due today
    attempts: 2,
    correctStreak: 0,
    lastCorrect: false,
    previousBid: '2S',
    correctBid: '2H',
    handData: {
      hand: [
        { rank: 'A', suit: 'S' },
        { rank: 'K', suit: 'S' },
        { rank: 'Q', suit: 'S' },
        { rank: 'J', suit: 'S' },
        { rank: '10', suit: 'S' },
        { rank: '6', suit: 'S' },
        { rank: '9', suit: 'H' },
        { rank: '5', suit: 'H' },
        { rank: 'K', suit: 'D' },
        { rank: '7', suit: 'D' },
        { rank: '4', suit: 'C' },
        { rank: '3', suit: 'C' },
        { rank: '2', suit: 'C' }
      ],
      auction: [
        { bid: '1NT', bidder: 'N', explanation: 'Balanced 15-17 HCP' }
      ],
      dealer: 'N',
      vulnerability: 'NS',
      hcp: 12
    },
    createdAt: addDays(getToday(), -5)
  },
  {
    handId: 'hand_003',
    decisionPoint: 'overcall_response',
    conventionTag: 'overcalls',
    category: 'competitive',
    intervalIndex: 0,
    nextReviewDate: addDays(getToday(), -1), // Overdue
    attempts: 1,
    correctStreak: 0,
    lastCorrect: false,
    previousBid: '2S',
    correctBid: '3S',
    handData: {
      hand: [
        { rank: 'Q', suit: 'S' },
        { rank: '10', suit: 'S' },
        { rank: '8', suit: 'S' },
        { rank: '4', suit: 'S' },
        { rank: 'K', suit: 'H' },
        { rank: '7', suit: 'H' },
        { rank: 'A', suit: 'D' },
        { rank: 'Q', suit: 'D' },
        { rank: '6', suit: 'D' },
        { rank: 'J', suit: 'C' },
        { rank: '9', suit: 'C' },
        { rank: '5', suit: 'C' },
        { rank: '3', suit: 'C' }
      ],
      auction: [
        { bid: '1H', bidder: 'E', explanation: 'Opening' },
        { bid: '1S', bidder: 'S', explanation: 'Overcall' },
        { bid: 'Pass', bidder: 'W', explanation: '' }
      ],
      dealer: 'E',
      vulnerability: 'EW',
      hcp: 12
    },
    createdAt: addDays(getToday(), -1)
  },
  {
    handId: 'hand_004',
    decisionPoint: 'opener_rebid',
    conventionTag: 'rebids',
    category: 'rebids',
    intervalIndex: 0,
    nextReviewDate: getToday(),
    attempts: 1,
    correctStreak: 0,
    lastCorrect: false,
    previousBid: '2H',
    correctBid: '3H',
    handData: {
      hand: [
        { rank: 'A', suit: 'S' },
        { rank: '8', suit: 'S' },
        { rank: 'A', suit: 'H' },
        { rank: 'K', suit: 'H' },
        { rank: 'Q', suit: 'H' },
        { rank: '9', suit: 'H' },
        { rank: '6', suit: 'H' },
        { rank: 'K', suit: 'D' },
        { rank: 'J', suit: 'D' },
        { rank: '5', suit: 'D' },
        { rank: 'Q', suit: 'C' },
        { rank: '8', suit: 'C' },
        { rank: '4', suit: 'C' }
      ],
      auction: [
        { bid: '1H', bidder: 'S', explanation: 'Opening' },
        { bid: 'Pass', bidder: 'W', explanation: '' },
        { bid: '2H', bidder: 'N', explanation: 'Simple raise, 6-10 points' },
        { bid: 'Pass', bidder: 'E', explanation: '' }
      ],
      dealer: 'S',
      vulnerability: 'Both',
      hcp: 17
    },
    createdAt: addDays(getToday(), -3)
  },
  {
    handId: 'hand_005',
    decisionPoint: 'blackwood_response',
    conventionTag: 'blackwood',
    category: 'slam',
    intervalIndex: 2,
    nextReviewDate: getToday(),
    attempts: 3,
    correctStreak: 1,
    lastCorrect: true,
    previousBid: '5C',
    correctBid: '5D',
    handData: {
      hand: [
        { rank: 'K', suit: 'S' },
        { rank: 'Q', suit: 'S' },
        { rank: 'J', suit: 'S' },
        { rank: '7', suit: 'S' },
        { rank: 'A', suit: 'H' },
        { rank: '9', suit: 'H' },
        { rank: '5', suit: 'H' },
        { rank: 'K', suit: 'D' },
        { rank: '10', suit: 'D' },
        { rank: '6', suit: 'D' },
        { rank: '8', suit: 'C' },
        { rank: '4', suit: 'C' },
        { rank: '2', suit: 'C' }
      ],
      auction: [
        { bid: '1S', bidder: 'N', explanation: 'Opening' },
        { bid: 'Pass', bidder: 'E', explanation: '' },
        { bid: '3S', bidder: 'S', explanation: 'Limit raise' },
        { bid: 'Pass', bidder: 'W', explanation: '' },
        { bid: '4NT', bidder: 'N', explanation: 'Blackwood - asking for aces' },
        { bid: 'Pass', bidder: 'E', explanation: '' }
      ],
      dealer: 'N',
      vulnerability: 'None',
      hcp: 11
    },
    createdAt: addDays(getToday(), -10)
  },
  {
    handId: 'hand_006',
    decisionPoint: 'opening_bid',
    conventionTag: 'opening',
    category: 'opening',
    intervalIndex: 0,
    nextReviewDate: addDays(getToday(), 1), // Due tomorrow (not shown in session)
    attempts: 0,
    correctStreak: 0,
    lastCorrect: false,
    previousBid: '1D',
    correctBid: '1NT',
    handData: {
      hand: [
        { rank: 'K', suit: 'S' },
        { rank: 'Q', suit: 'S' },
        { rank: '10', suit: 'S' },
        { rank: 'A', suit: 'H' },
        { rank: 'J', suit: 'H' },
        { rank: '8', suit: 'H' },
        { rank: 'K', suit: 'D' },
        { rank: 'Q', suit: 'D' },
        { rank: '6', suit: 'D' },
        { rank: '5', suit: 'D' },
        { rank: 'Q', suit: 'C' },
        { rank: '9', suit: 'C' },
        { rank: '3', suit: 'C' }
      ],
      auction: [],
      dealer: 'S',
      vulnerability: 'NS',
      hcp: 16
    },
    createdAt: addDays(getToday(), -1)
  }
];

/**
 * Category display names and descriptions
 */
export const CATEGORY_INFO = {
  responses: {
    name: 'Responses to Opening',
    description: 'Responding to partner\'s opening bid'
  },
  rebids: {
    name: 'Opener Rebids',
    description: 'Second bid by the opening bidder'
  },
  competitive: {
    name: 'Competitive Bidding',
    description: 'Overcalls and competitive sequences'
  },
  slam: {
    name: 'Slam Bidding',
    description: 'Blackwood, Gerber, and slam exploration'
  },
  opening: {
    name: 'Opening Bids',
    description: 'Choosing the correct opening bid'
  },
  other: {
    name: 'Other',
    description: 'Miscellaneous bidding situations'
  }
};

/**
 * Load mock data into localStorage for testing
 */
export const initializeMockData = () => {
  // Only load if no existing data
  const existing = localStorage.getItem('mbb-review-queue');
  if (!existing || JSON.parse(existing).length === 0) {
    localStorage.setItem('mbb-review-queue', JSON.stringify(MOCK_REVIEW_ITEMS));
    return true;
  }
  return false;
};

/**
 * Reset to mock data (for testing)
 */
export const resetToMockData = () => {
  localStorage.setItem('mbb-review-queue', JSON.stringify(MOCK_REVIEW_ITEMS));
};
