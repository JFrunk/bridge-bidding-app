/**
 * mockData.js
 *
 * Sample auctions with all four hands for the Guess Partner's Hand flow.
 * Each scenario includes a complete auction and all four hands for reveal.
 *
 * Player is always South, partner is always North.
 */

/**
 * @typedef {Object} MockScenario
 * @property {string} id - Unique scenario identifier
 * @property {string} title - Human-readable title
 * @property {string} description - Brief description of the scenario
 * @property {string} dealer - Who dealt ('N', 'E', 'S', 'W')
 * @property {Array<{bid: string, bidder: string, explanation?: string}>} auction - Complete auction
 * @property {Object} hands - All four hands
 * @property {Array} hands.north - North's 13 cards (partner)
 * @property {Array} hands.east - East's 13 cards
 * @property {Array} hands.south - South's 13 cards (player)
 * @property {Array} hands.west - West's 13 cards
 */

/**
 * Scenario 1: Simple 1NT Opening
 * Partner opens 1NT showing 15-17 HCP, balanced shape.
 * Player should estimate HCP 15-17, balanced shape.
 */
export const SCENARIO_1NT_OPENING = {
  id: 'scenario-1nt-opening',
  title: 'Simple 1NT Opening',
  description: 'Partner opens 1NT. What does their hand look like?',
  dealer: 'N',
  auction: [
    { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
    { bid: 'Pass', bidder: 'E' },
    { bid: 'Pass', bidder: 'S' },
    { bid: 'Pass', bidder: 'W' },
  ],
  hands: {
    north: [
      { rank: 'A', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: '10', suit: 'C' },
      { rank: '5', suit: 'C' },
      { rank: '3', suit: 'C' },
    ],
    east: [
      { rank: '9', suit: 'S' },
      { rank: '8', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: '4', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: 'J', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: 'Q', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '6', suit: 'C' },
    ],
    south: [
      { rank: '6', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: '9', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: 'K', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '4', suit: 'C' },
      { rank: '2', suit: 'C' },
    ],
    west: [
      { rank: 'K', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '7', suit: 'H' },
      { rank: '4', suit: 'D' },
      { rank: '3', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: '8', suit: 'C' },
    ],
  },
};

/**
 * Scenario 2: 1S Opening with Game-Forcing Response
 * Partner opens 1S, shows 5+ spades, 12-21 HCP.
 * After responder's 2D game-force, partner shows extra values.
 */
export const SCENARIO_1S_GAME_FORCE = {
  id: 'scenario-1s-gf',
  title: '1S Opening with Game Force',
  description: 'Partner opens 1S and later shows extra values.',
  dealer: 'N',
  auction: [
    { bid: '1S', bidder: 'N', explanation: '5+ spades, 12-21 HCP' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '2D', bidder: 'S', explanation: 'Game forcing, 4+ diamonds' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '3S', bidder: 'N', explanation: '6+ spades, extra values' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '4S', bidder: 'S' },
    { bid: 'Pass', bidder: 'W' },
    { bid: 'Pass', bidder: 'N' },
    { bid: 'Pass', bidder: 'E' },
  ],
  hands: {
    north: [
      { rank: 'A', suit: 'S' },
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: 'Q', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: '4', suit: 'C' },
    ],
    east: [
      { rank: '10', suit: 'S' },
      { rank: '9', suit: 'S' },
      { rank: '4', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '2', suit: 'C' },
    ],
    south: [
      { rank: '3', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: 'J', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: '10', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '5', suit: 'C' },
    ],
    west: [
      { rank: '8', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '9', suit: 'H' },
      { rank: '7', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: '3', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: '3', suit: 'C' },
    ],
  },
};

/**
 * Scenario 3: Competitive Auction (Opponent Overcalls)
 * Partner opens 1H, opponent overcalls 2C.
 * Partner's double shows extra values and support.
 */
export const SCENARIO_COMPETITIVE = {
  id: 'scenario-competitive',
  title: 'Competitive Auction',
  description: 'Partner opens 1H, opponent overcalls. Partner shows extras.',
  dealer: 'N',
  auction: [
    { bid: '1H', bidder: 'N', explanation: '5+ hearts, 12-21 HCP' },
    { bid: '2C', bidder: 'E', explanation: 'Overcall, 5+ clubs' },
    { bid: '2H', bidder: 'S', explanation: 'Simple raise, 6-9 HCP' },
    { bid: '3C', bidder: 'W', explanation: 'Competitive raise' },
    { bid: '3H', bidder: 'N', explanation: 'Competitive, extra values' },
    { bid: 'Pass', bidder: 'E' },
    { bid: 'Pass', bidder: 'S' },
    { bid: 'Pass', bidder: 'W' },
  ],
  hands: {
    north: [
      { rank: 'K', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '9', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: '8', suit: 'C' },
      { rank: '3', suit: 'C' },
    ],
    east: [
      { rank: '9', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: '8', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: '6', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: 'K', suit: 'C' },
      { rank: 'Q', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '10', suit: 'C' },
      { rank: '6', suit: 'C' },
    ],
    south: [
      { rank: '8', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '7', suit: 'H' },
      { rank: 'Q', suit: 'D' },
      { rank: 'J', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '9', suit: 'C' },
      { rank: '5', suit: 'C' },
      { rank: '4', suit: 'C' },
    ],
    west: [
      { rank: 'A', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '5', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: '8', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '3', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: '7', suit: 'C' },
      { rank: '2', suit: 'C' },
    ],
  },
};

/**
 * Scenario 4: Slam Try Sequence
 * Partner opens 2C (strong), shows 22+ HCP or game forcing.
 * Auction proceeds through Blackwood to 6NT.
 */
export const SCENARIO_SLAM_TRY = {
  id: 'scenario-slam-try',
  title: 'Slam Try Sequence',
  description: 'Partner opens 2C and the auction heads toward slam.',
  dealer: 'N',
  auction: [
    { bid: '2C', bidder: 'N', explanation: '22+ HCP or game forcing' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '2D', bidder: 'S', explanation: 'Waiting, artificial' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '2NT', bidder: 'N', explanation: '22-24 HCP, balanced' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '4NT', bidder: 'S', explanation: 'RKCB for NT' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '5H', bidder: 'N', explanation: '2 key cards without Q' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '6NT', bidder: 'S' },
    { bid: 'Pass', bidder: 'W' },
    { bid: 'Pass', bidder: 'N' },
    { bid: 'Pass', bidder: 'E' },
  ],
  hands: {
    north: [
      { rank: 'A', suit: 'S' },
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'J', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: 'Q', suit: 'C' },
    ],
    east: [
      { rank: '10', suit: 'S' },
      { rank: '9', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '10', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: '8', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: '9', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '5', suit: 'C' },
    ],
    south: [
      { rank: 'J', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '9', suit: 'H' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '10', suit: 'C' },
      { rank: '4', suit: 'C' },
    ],
    west: [
      { rank: '8', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: '7', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: '5', suit: 'D' },
      { rank: '3', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: '8', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '3', suit: 'C' },
      { rank: '2', suit: 'C' },
    ],
  },
};

/**
 * Scenario 5: Passed-Out Then Balance
 * Auction passes to partner in 4th seat who balances with 1S.
 * Balancing shows about 10-14 HCP typically.
 */
export const SCENARIO_BALANCE = {
  id: 'scenario-balance',
  title: 'Balancing Bid',
  description: 'After three passes, partner balances with 1S.',
  dealer: 'E',
  auction: [
    { bid: 'Pass', bidder: 'E' },
    { bid: 'Pass', bidder: 'S' },
    { bid: 'Pass', bidder: 'W' },
    { bid: '1S', bidder: 'N', explanation: 'Balancing, 10-14 HCP, 5+ spades' },
    { bid: 'Pass', bidder: 'E' },
    { bid: '2S', bidder: 'S', explanation: 'Simple raise' },
    { bid: 'Pass', bidder: 'W' },
    { bid: 'Pass', bidder: 'N' },
    { bid: 'Pass', bidder: 'E' },
  ],
  hands: {
    north: [
      { rank: 'A', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '8', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: '7', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: '10', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: 'Q', suit: 'C' },
      { rank: '4', suit: 'C' },
    ],
    east: [
      { rank: '5', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '9', suit: 'C' },
    ],
    south: [
      { rank: 'K', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '9', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: '8', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '3', suit: 'C' },
    ],
    west: [
      { rank: '9', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: 'J', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '3', suit: 'D' },
      { rank: '2', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: '10', suit: 'C' },
      { rank: '5', suit: 'C' },
      { rank: '2', suit: 'C' },
    ],
  },
};

/**
 * All scenarios in order
 */
export const ALL_SCENARIOS = [
  SCENARIO_1NT_OPENING,
  SCENARIO_1S_GAME_FORCE,
  SCENARIO_COMPETITIVE,
  SCENARIO_SLAM_TRY,
  SCENARIO_BALANCE,
];

/**
 * Get a random scenario
 * @returns {Object} A random scenario from the list
 */
export const getRandomScenario = () => {
  const index = Math.floor(Math.random() * ALL_SCENARIOS.length);
  return ALL_SCENARIOS[index];
};

/**
 * Get scenario by ID
 * @param {string} id - Scenario ID
 * @returns {Object|undefined} The matching scenario or undefined
 */
export const getScenarioById = (id) => {
  return ALL_SCENARIOS.find(s => s.id === id);
};

export default ALL_SCENARIOS;
