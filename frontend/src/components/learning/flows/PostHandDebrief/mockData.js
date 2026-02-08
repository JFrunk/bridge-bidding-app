/**
 * mockData.js
 *
 * Sample completed hands for PostHandDebrief flow testing.
 * Three scenarios covering different outcomes:
 * 1. Perfect bidding but lost a trick in play
 * 2. Bidding mistake led to wrong contract
 * 3. Everything optimal (positive reinforcement)
 */

/**
 * Hand 1: Perfect bidding, play error
 * - Correct bidding sequence to 3NT
 * - User failed to hold up ace in defense (lost a trick)
 */
export const handPerfectBiddingPlayError = {
  handId: 'debrief_001',
  boardNumber: 47,
  allHands: {
    north: [
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: '7', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: 'Q', suit: 'D' },
      { rank: 'J', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '4', suit: 'C' }
    ],
    east: [
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '8', suit: 'S' },
      { rank: '6', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: 'Q', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '10', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: '8', suit: 'C' }
    ],
    south: [
      { rank: 'A', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '9', suit: 'H' },
      { rank: 'K', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '5', suit: 'C' },
      { rank: '2', suit: 'C' }
    ],
    west: [
      { rank: '9', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: '10', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: '5', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: '3', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: '3', suit: 'C' }
    ]
  },
  auction: [
    { bid: '1NT', bidder: 'S', explanation: 'Balanced 15-17 HCP' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '3NT', bidder: 'N', explanation: 'Game values, balanced' },
    { bid: 'Pass', bidder: 'E' },
    { bid: 'Pass', bidder: 'S' },
    { bid: 'Pass', bidder: 'W' }
  ],
  contract: {
    level: 3,
    strain: 'NT',
    declarer: 'S',
    doubled: false,
    redoubled: false
  },
  result: {
    tricksRequired: 9,
    tricksMade: 10,
    overtricks: 1,
    score: 430,
    vulnerability: 'None'
  },
  decisions: [
    {
      decisionId: 'bid_1',
      round: 1,
      type: 'bid',
      position: 'S',
      playerAction: '1NT',
      optimalAction: '1NT',
      isCorrect: true,
      explanation: 'Balanced hand with 15-17 HCP. Perfect 1NT opening.'
    },
    {
      decisionId: 'bid_2',
      round: 2,
      type: 'bid',
      position: 'N',
      playerAction: '3NT',
      optimalAction: '3NT',
      isCorrect: true,
      explanation: 'With 14 HCP opposite 15-17, you have game values. 3NT is correct.'
    },
    {
      decisionId: 'play_1',
      round: 3,
      type: 'play',
      position: 'S',
      playerAction: 'Won trick 1',
      optimalAction: 'Duck spade lead',
      isCorrect: false,
      explanation: 'Holding up the ace on trick 1 would have blocked the spade suit.'
    }
  ]
};

/**
 * Hand 2: Bidding mistake led to wrong contract
 * - User opened 1H with unbalanced hand (correct)
 * - User rebid 2H instead of 3H (mistake - shows 6 cards but minimum)
 * - Missed game due to underbid
 */
export const handBiddingMistake = {
  handId: 'debrief_002',
  boardNumber: 52,
  allHands: {
    north: [
      { rank: 'A', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: '9', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: 'Q', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: '5', suit: 'C' }
    ],
    east: [
      { rank: 'Q', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '9', suit: 'S' },
      { rank: '4', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'J', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: 'Q', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: '3', suit: 'C' }
    ],
    south: [
      { rank: '8', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: 'K', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: 'J', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '2', suit: 'C' }
    ],
    west: [
      { rank: 'K', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: '7', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: '8', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: '3', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: '10', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '4', suit: 'C' }
    ]
  },
  auction: [
    { bid: '1H', bidder: 'S', explanation: '6-card heart suit, 12 HCP' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '2H', bidder: 'N', explanation: 'Heart support, 10-12 points' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '2H', bidder: 'S', explanation: 'Player rebid - minimum' },
    { bid: 'Pass', bidder: 'W' },
    { bid: 'Pass', bidder: 'N' },
    { bid: 'Pass', bidder: 'E' }
  ],
  contract: {
    level: 2,
    strain: 'H',
    declarer: 'S',
    doubled: false,
    redoubled: false
  },
  result: {
    tricksRequired: 8,
    tricksMade: 10,
    overtricks: 2,
    score: 170,
    vulnerability: 'None'
  },
  decisions: [
    {
      decisionId: 'bid_1',
      round: 1,
      type: 'bid',
      position: 'S',
      playerAction: '1H',
      optimalAction: '1H',
      isCorrect: true,
      explanation: 'Correct opening with 6-card heart suit and 12 HCP.'
    },
    {
      decisionId: 'bid_2',
      round: 2,
      type: 'bid',
      position: 'S',
      playerAction: '2H',
      optimalAction: '3H',
      isCorrect: false,
      explanation: 'With 6 hearts and a singleton, you should jump to 3H to show extras. Partner\'s raise shows 3+ hearts and 6-9 points.'
    },
    {
      decisionId: 'play_1',
      round: 3,
      type: 'result',
      position: 'S',
      playerAction: 'Made +2',
      optimalAction: '4H Game',
      isCorrect: false,
      explanation: 'The +2 overtricks show 4H would have made. Missed 420 points vs 170 scored.'
    }
  ]
};

/**
 * Hand 3: Everything optimal (positive reinforcement)
 * - Correct Stayman sequence
 * - Found 4-4 spade fit
 * - Made contract exactly
 */
export const handEverythingOptimal = {
  handId: 'debrief_003',
  boardNumber: 61,
  allHands: {
    north: [
      { rank: 'Q', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: 'Q', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '3', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: '4', suit: 'C' }
    ],
    east: [
      { rank: '6', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: '4', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: 'Q', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '10', suit: 'C' },
      { rank: '5', suit: 'C' }
    ],
    south: [
      { rank: 'A', suit: 'S' },
      { rank: 'K', suit: 'S' },
      { rank: '9', suit: 'S' },
      { rank: '8', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: 'J', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '2', suit: 'C' }
    ],
    west: [
      { rank: '4', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: '9', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: '7', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: '10', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: '9', suit: 'C' },
      { rank: '3', suit: 'C' }
    ]
  },
  auction: [
    { bid: '1NT', bidder: 'S', explanation: 'Balanced 15-17 HCP' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '2C', bidder: 'N', explanation: 'Stayman - asking for 4-card major' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '2S', bidder: 'S', explanation: 'Shows 4 spades' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '4S', bidder: 'N', explanation: 'Game in spades with 4-4 fit' },
    { bid: 'Pass', bidder: 'E' },
    { bid: 'Pass', bidder: 'S' },
    { bid: 'Pass', bidder: 'W' }
  ],
  contract: {
    level: 4,
    strain: 'S',
    declarer: 'S',
    doubled: false,
    redoubled: false
  },
  result: {
    tricksRequired: 10,
    tricksMade: 10,
    overtricks: 0,
    score: 420,
    vulnerability: 'None'
  },
  decisions: [
    {
      decisionId: 'bid_1',
      round: 1,
      type: 'bid',
      position: 'S',
      playerAction: '1NT',
      optimalAction: '1NT',
      isCorrect: true,
      explanation: 'Balanced 15-17 HCP. Perfect 1NT opening.'
    },
    {
      decisionId: 'bid_2',
      round: 2,
      type: 'bid',
      position: 'N',
      playerAction: '2C',
      optimalAction: '2C',
      isCorrect: true,
      explanation: 'Stayman with 4 spades and game values. Looking for a major suit fit.'
    },
    {
      decisionId: 'bid_3',
      round: 3,
      type: 'bid',
      position: 'S',
      playerAction: '2S',
      optimalAction: '2S',
      isCorrect: true,
      explanation: 'Correctly showed 4 spades in response to Stayman.'
    },
    {
      decisionId: 'bid_4',
      round: 4,
      type: 'bid',
      position: 'N',
      playerAction: '4S',
      optimalAction: '4S',
      isCorrect: true,
      explanation: 'Bid game with 4-4 spade fit and 14 HCP opposite 15-17.'
    },
    {
      decisionId: 'play_1',
      round: 5,
      type: 'result',
      position: 'S',
      playerAction: 'Made exactly',
      optimalAction: 'Made exactly',
      isCorrect: true,
      explanation: 'Made the contract exactly. Well played!'
    }
  ]
};

/**
 * All mock hands for iteration
 */
export const mockDebriefHands = [
  handPerfectBiddingPlayError,
  handBiddingMistake,
  handEverythingOptimal
];

export default mockDebriefHands;
