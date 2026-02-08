/**
 * Mock Data for Opening Lead Quiz
 *
 * 5 sample hands with DDS lead evaluations demonstrating different lead scenarios:
 * 1. Top-of-sequence is correct
 * 2. Passive lead beats aggressive
 * 3. Leading partner's suit is correct
 * 4. Leading trumps is correct
 * 5. Unusual lead (underlead ace) is correct
 */

/**
 * @typedef {Object} LeadEvaluation
 * @property {string} card - Card notation e.g. "KS" for King of Spades
 * @property {number} defensiveTricks - Expected defensive tricks with this lead
 * @property {string} contractResult - Result string e.g. "Down 1", "Making"
 */

/**
 * @typedef {Object} MockHand
 * @property {string} id - Unique identifier
 * @property {string} title - Scenario title
 * @property {string} description - Brief description of the scenario
 * @property {'W' | 'E'} leader - Which defender is on lead
 * @property {Object} contract - Contract information
 * @property {Array} auction - Auction history
 * @property {Object} hands - All four hands
 * @property {Array<LeadEvaluation>} leadEvaluations - DDS results for each lead
 * @property {string} optimalLead - The best lead card
 * @property {string} explanation - Explanation of why the optimal lead is best
 */

export const MOCK_HANDS = [
  // Scenario 1: Top-of-sequence is correct (KQJ lead)
  {
    id: 'lead-001',
    title: 'Top of Sequence',
    description: 'A classic top-of-sequence lead from KQJ',
    leader: 'W',
    contract: {
      level: 4,
      strain: 'S',
      declarer: 'S',
      doubled: false,
      redoubled: false
    },
    auction: [
      { bid: '1S', bidder: 'S', explanation: 'Opening bid' },
      { bid: 'Pass', bidder: 'W' },
      { bid: '2NT', bidder: 'N', explanation: 'Jacoby 2NT' },
      { bid: 'Pass', bidder: 'E' },
      { bid: '4S', bidder: 'S', explanation: 'Minimum with no shortness' },
      { bid: 'Pass', bidder: 'W' },
      { bid: 'Pass', bidder: 'N' },
      { bid: 'Pass', bidder: 'E' }
    ],
    hands: {
      north: [
        { rank: 'A', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '5', suit: 'S' },
        { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '8', suit: 'H' },
        { rank: 'A', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '6', suit: 'D' },
        { rank: '7', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' }
      ],
      east: [
        { rank: '8', suit: 'S' }, { rank: '3', suit: 'S' },
        { rank: '10', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' },
        { rank: 'Q', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '8', suit: 'D' },
        { rank: 'K', suit: 'C' }, { rank: '10', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '5', suit: 'C' }, { rank: '3', suit: 'C' }
      ],
      south: [
        { rank: 'K', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '10', suit: 'S' },
        { rank: '9', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '6', suit: 'S' },
        { rank: 'A', suit: 'H' }, { rank: '5', suit: 'H' },
        { rank: 'K', suit: 'D' }, { rank: '10', suit: 'D' }, { rank: '4', suit: 'D' },
        { rank: 'A', suit: 'C' }, { rank: '8', suit: 'C' }
      ],
      west: [
        { rank: '4', suit: 'S' }, { rank: '2', suit: 'S' },
        { rank: 'J', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' }, { rank: '2', suit: 'H' },
        { rank: '7', suit: 'D' }, { rank: '5', suit: 'D' }, { rank: '3', suit: 'D' }, { rank: '2', suit: 'D' },
        { rank: 'Q', suit: 'C' }, { rank: 'J', suit: 'C' }
      ]
    },
    leadEvaluations: [
      { card: { rank: 'Q', suit: 'C' }, defensiveTricks: 4, contractResult: 'Down 1' },
      { card: { rank: 'J', suit: 'C' }, defensiveTricks: 3, contractResult: 'Making' },
      { card: { rank: 'J', suit: 'H' }, defensiveTricks: 3, contractResult: 'Making' },
      { card: { rank: '4', suit: 'S' }, defensiveTricks: 2, contractResult: 'Making +1' },
      { card: { rank: '7', suit: 'D' }, defensiveTricks: 3, contractResult: 'Making' }
    ],
    optimalLead: { rank: 'Q', suit: 'C' },
    explanation: 'Lead the Queen from QJ sequence. Top-of-sequence leads are safe and establish tricks without giving up tempo. The QJ combination in clubs sets up a quick trick and may find partner with the King.'
  },

  // Scenario 2: Passive lead beats aggressive
  {
    id: 'lead-002',
    title: 'Passive Defense',
    description: 'When in doubt, lead passively',
    leader: 'W',
    contract: {
      level: 3,
      strain: 'NT',
      declarer: 'S',
      doubled: false,
      redoubled: false
    },
    auction: [
      { bid: '1NT', bidder: 'S', explanation: '15-17 HCP' },
      { bid: 'Pass', bidder: 'W' },
      { bid: '3NT', bidder: 'N', explanation: 'To play' },
      { bid: 'Pass', bidder: 'E' },
      { bid: 'Pass', bidder: 'S' },
      { bid: 'Pass', bidder: 'W' }
    ],
    hands: {
      north: [
        { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '6', suit: 'S' },
        { rank: 'K', suit: 'H' }, { rank: '10', suit: 'H' }, { rank: '8', suit: 'H' },
        { rank: 'Q', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '5', suit: 'D' },
        { rank: 'K', suit: 'C' }, { rank: 'J', suit: 'C' }, { rank: '7', suit: 'C' }, { rank: '3', suit: 'C' }
      ],
      east: [
        { rank: '10', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
        { rank: 'Q', suit: 'H' }, { rank: '5', suit: 'H' }, { rank: '4', suit: 'H' },
        { rank: 'K', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '8', suit: 'D' },
        { rank: '10', suit: 'C' }, { rank: '8', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '4', suit: 'C' }
      ],
      south: [
        { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: '9', suit: 'S' },
        { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '7', suit: 'H' },
        { rank: 'A', suit: 'D' }, { rank: '10', suit: 'D' }, { rank: '4', suit: 'D' },
        { rank: 'A', suit: 'C' }, { rank: 'Q', suit: 'C' }, { rank: '5', suit: 'C' }, { rank: '2', suit: 'C' }
      ],
      west: [
        { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' }, { rank: '3', suit: 'S' }, { rank: '2', suit: 'S' },
        { rank: '9', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' }, { rank: '2', suit: 'H' },
        { rank: '7', suit: 'D' }, { rank: '6', suit: 'D' }, { rank: '3', suit: 'D' }, { rank: '2', suit: 'D' },
        { rank: '9', suit: 'C' }
      ]
    },
    leadEvaluations: [
      { card: { rank: '3', suit: 'S' }, defensiveTricks: 4, contractResult: 'Down 1' },
      { card: { rank: '3', suit: 'H' }, defensiveTricks: 3, contractResult: 'Making' },
      { card: { rank: '7', suit: 'D' }, defensiveTricks: 3, contractResult: 'Making' },
      { card: { rank: '9', suit: 'C' }, defensiveTricks: 2, contractResult: 'Making +1' }
    ],
    optimalLead: { rank: '3', suit: 'S' },
    explanation: 'Lead a passive spade from small cards. Against 3NT with no suit bid by partner, lead your longest suit passively. Do not give away tricks by leading from broken honor holdings. Let declarer do the work.'
  },

  // Scenario 3: Leading partner's suit is correct
  {
    id: 'lead-003',
    title: "Partner's Suit",
    description: 'Lead partner\'s overcalled suit',
    leader: 'W',
    contract: {
      level: 4,
      strain: 'H',
      declarer: 'S',
      doubled: false,
      redoubled: false
    },
    auction: [
      { bid: '1H', bidder: 'S', explanation: 'Opening bid' },
      { bid: '2D', bidder: 'W', explanation: 'Overcall' },
      { bid: '2H', bidder: 'N', explanation: 'Raise' },
      { bid: 'Pass', bidder: 'E' },
      { bid: '4H', bidder: 'S', explanation: 'Game' },
      { bid: 'Pass', bidder: 'W' },
      { bid: 'Pass', bidder: 'N' },
      { bid: 'Pass', bidder: 'E' }
    ],
    hands: {
      north: [
        { rank: 'Q', suit: 'S' }, { rank: '10', suit: 'S' }, { rank: '5', suit: 'S' },
        { rank: 'K', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' },
        { rank: '8', suit: 'D' }, { rank: '5', suit: 'D' },
        { rank: 'K', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '3', suit: 'C' }
      ],
      east: [
        { rank: '9', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' }, { rank: '3', suit: 'S' },
        { rank: '6', suit: 'H' }, { rank: '5', suit: 'H' },
        { rank: 'A', suit: 'D' }, { rank: '10', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '4', suit: 'D' },
        { rank: 'Q', suit: 'C' }, { rank: '10', suit: 'C' }, { rank: '5', suit: 'C' }
      ],
      south: [
        { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: '8', suit: 'S' },
        { rank: 'A', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: 'J', suit: 'H' },
        { rank: '10', suit: 'H' }, { rank: '3', suit: 'H' },
        { rank: '7', suit: 'D' },
        { rank: 'A', suit: 'C' }, { rank: '8', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' }
      ],
      west: [
        { rank: 'J', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '2', suit: 'S' },
        { rank: '8', suit: 'H' }, { rank: '2', suit: 'H' },
        { rank: 'K', suit: 'D' }, { rank: 'Q', suit: 'D' }, { rank: 'J', suit: 'D' },
        { rank: '6', suit: 'D' }, { rank: '3', suit: 'D' }, { rank: '2', suit: 'D' },
        { rank: 'J', suit: 'C' }, { rank: '7', suit: 'C' }
      ]
    },
    leadEvaluations: [
      { card: { rank: 'K', suit: 'D' }, defensiveTricks: 4, contractResult: 'Down 1' },
      { card: { rank: 'J', suit: 'S' }, defensiveTricks: 2, contractResult: 'Making +1' },
      { card: { rank: 'J', suit: 'C' }, defensiveTricks: 3, contractResult: 'Making' },
      { card: { rank: '8', suit: 'H' }, defensiveTricks: 2, contractResult: 'Making +1' }
    ],
    optimalLead: { rank: 'K', suit: 'D' },
    explanation: 'Lead the King of diamonds - the top of your sequence in the suit you overcalled. You bid diamonds to help partner find the right lead. With KQJ, you can establish diamond tricks before declarer draws trumps.'
  },

  // Scenario 4: Leading trumps is correct
  {
    id: 'lead-004',
    title: 'Trump Lead',
    description: 'Cut down ruffs with a trump lead',
    leader: 'W',
    contract: {
      level: 2,
      strain: 'S',
      declarer: 'S',
      doubled: false,
      redoubled: false
    },
    auction: [
      { bid: '1H', bidder: 'S', explanation: 'Opening bid' },
      { bid: 'Pass', bidder: 'W' },
      { bid: '1S', bidder: 'N', explanation: 'New suit' },
      { bid: 'Pass', bidder: 'E' },
      { bid: '2S', bidder: 'S', explanation: 'Support with 3 cards' },
      { bid: 'Pass', bidder: 'W' },
      { bid: 'Pass', bidder: 'N' },
      { bid: 'Pass', bidder: 'E' }
    ],
    hands: {
      north: [
        { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '8', suit: 'S' },
        { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
        { rank: '10', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '5', suit: 'H' },
        { rank: '9', suit: 'D' }, { rank: '4', suit: 'D' },
        { rank: 'Q', suit: 'C' }, { rank: 'J', suit: 'C' }, { rank: '5', suit: 'C' }
      ],
      east: [
        { rank: '10', suit: 'S' }, { rank: '5', suit: 'S' },
        { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '4', suit: 'H' },
        { rank: 'Q', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '10', suit: 'D' },
        { rank: '6', suit: 'D' }, { rank: '3', suit: 'D' },
        { rank: 'K', suit: 'C' }, { rank: '7', suit: 'C' }, { rank: '2', suit: 'C' }
      ],
      south: [
        { rank: 'A', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '3', suit: 'S' },
        { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '9', suit: 'H' },
        { rank: '8', suit: 'H' }, { rank: '7', suit: 'H' },
        { rank: 'A', suit: 'D' }, { rank: '5', suit: 'D' },
        { rank: 'A', suit: 'C' }, { rank: '8', suit: 'C' }, { rank: '6', suit: 'C' }
      ],
      west: [
        { rank: '9', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '2', suit: 'S' },
        { rank: '3', suit: 'H' }, { rank: '2', suit: 'H' },
        { rank: 'K', suit: 'D' }, { rank: '8', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '2', suit: 'D' },
        { rank: '10', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '3', suit: 'C' }
      ]
    },
    leadEvaluations: [
      { card: { rank: '9', suit: 'S' }, defensiveTricks: 6, contractResult: 'Down 2' },
      { card: { rank: '3', suit: 'H' }, defensiveTricks: 4, contractResult: 'Making' },
      { card: { rank: 'K', suit: 'D' }, defensiveTricks: 4, contractResult: 'Making' },
      { card: { rank: '10', suit: 'C' }, defensiveTricks: 5, contractResult: 'Down 1' }
    ],
    optimalLead: { rank: '9', suit: 'S' },
    explanation: 'Lead a trump! Declarer has a two-suited hand (hearts and spades) and will try to ruff hearts in dummy. Leading trumps cuts down ruffs and forces declarer to lose control. Each trump lead is worth an extra trick on defense.'
  },

  // Scenario 5: Unusual lead (underlead ace) is correct
  {
    id: 'lead-005',
    title: 'Aggressive Underlead',
    description: 'Underlead an ace to find partner\'s King',
    leader: 'W',
    contract: {
      level: 6,
      strain: 'H',
      declarer: 'S',
      doubled: false,
      redoubled: false
    },
    auction: [
      { bid: '1H', bidder: 'S', explanation: 'Opening bid' },
      { bid: 'Pass', bidder: 'W' },
      { bid: '2NT', bidder: 'N', explanation: 'Jacoby 2NT - forcing' },
      { bid: 'Pass', bidder: 'E' },
      { bid: '3D', bidder: 'S', explanation: 'Diamond shortness' },
      { bid: 'Pass', bidder: 'W' },
      { bid: '4NT', bidder: 'N', explanation: 'Blackwood' },
      { bid: 'Pass', bidder: 'E' },
      { bid: '5D', bidder: 'S', explanation: '1 keycard' },
      { bid: 'Pass', bidder: 'W' },
      { bid: '6H', bidder: 'N', explanation: 'Small slam' },
      { bid: 'Pass', bidder: 'E' },
      { bid: 'Pass', bidder: 'S' },
      { bid: 'Pass', bidder: 'W' }
    ],
    hands: {
      north: [
        { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '7', suit: 'S' },
        { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '9', suit: 'H' },
        { rank: '9', suit: 'D' }, { rank: '5', suit: 'D' },
        { rank: 'A', suit: 'C' }, { rank: 'Q', suit: 'C' }, { rank: 'J', suit: 'C' }, { rank: '4', suit: 'C' }
      ],
      east: [
        { rank: '9', suit: 'S' }, { rank: '5', suit: 'S' }, { rank: '4', suit: 'S' },
        { rank: '6', suit: 'H' }, { rank: '4', suit: 'H' },
        { rank: 'K', suit: 'D' }, { rank: 'Q', suit: 'D' }, { rank: 'J', suit: 'D' },
        { rank: '10', suit: 'D' }, { rank: '7', suit: 'D' },
        { rank: '9', suit: 'C' }, { rank: '7', suit: 'C' }, { rank: '5', suit: 'C' }
      ],
      south: [
        { rank: 'A', suit: 'S' }, { rank: '10', suit: 'S' }, { rank: '8', suit: 'S' },
        { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '10', suit: 'H' },
        { rank: '8', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '5', suit: 'H' },
        { rank: '2', suit: 'D' },
        { rank: 'K', suit: 'C' }, { rank: '10', suit: 'C' }, { rank: '3', suit: 'C' }
      ],
      west: [
        { rank: '6', suit: 'S' }, { rank: '3', suit: 'S' }, { rank: '2', suit: 'S' },
        { rank: '3', suit: 'H' }, { rank: '2', suit: 'H' },
        { rank: 'A', suit: 'D' }, { rank: '8', suit: 'D' }, { rank: '6', suit: 'D' },
        { rank: '4', suit: 'D' }, { rank: '3', suit: 'D' },
        { rank: '8', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '2', suit: 'C' }
      ]
    },
    leadEvaluations: [
      { card: { rank: '8', suit: 'D' }, defensiveTricks: 2, contractResult: 'Down 1' },
      { card: { rank: 'A', suit: 'D' }, defensiveTricks: 1, contractResult: 'Making' },
      { card: { rank: '6', suit: 'S' }, defensiveTricks: 1, contractResult: 'Making' },
      { card: { rank: '8', suit: 'C' }, defensiveTricks: 1, contractResult: 'Making' },
      { card: { rank: '3', suit: 'H' }, defensiveTricks: 0, contractResult: 'Making +1' }
    ],
    optimalLead: { rank: '8', suit: 'D' },
    explanation: 'Underlead your Ace of diamonds! Declarer showed diamond shortness (singleton or void). Partner likely has diamond honors including the King. Leading low lets partner win the King and return the suit for your Ace. Leading the Ace wastes a trick when partner has KQJ.'
  }
];

export default MOCK_HANDS;
