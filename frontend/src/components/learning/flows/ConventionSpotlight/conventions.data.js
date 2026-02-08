/**
 * conventions.data.js
 *
 * Convention definitions and drill hands for the Convention Spotlight flow.
 * Each convention includes quick reference material and drill hands for practice.
 *
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

/**
 * Convention categories
 */
export const CONVENTION_CATEGORIES = {
  RESPONSES: 'responses',
  DOUBLES: 'doubles',
  SLAM: 'slam',
  CONSTRUCTIVE: 'constructive',
  COMPETITIVE: 'competitive',
};

/**
 * Question types for drill hands
 */
export const QUESTION_TYPES = {
  YES_NO: 'yes_no',        // "Should you bid Stayman?" -> Yes/No
  BID_CHOICE: 'bid_choice', // "What's your next bid?" -> Multiple bid choices
  FOLLOW_UP: 'follow_up',   // Follow-up question after initial convention use
};

/**
 * Convention data with drill hands
 * Each convention has:
 * - id: Unique identifier
 * - name: Display name
 * - category: Convention category
 * - quickRef: Quick reference information
 * - drillHands: Array of drill scenarios
 */
export const CONVENTIONS = [
  // ============================================
  // 1. STAYMAN
  // ============================================
  {
    id: 'stayman',
    name: 'Stayman (2\u2663)',
    category: CONVENTION_CATEGORIES.RESPONSES,
    quickRef: {
      whenToUse: 'After partner opens 1NT (15-17 HCP), bid 2\u2663 to ask for a 4-card major. Requires 8+ HCP and at least one 4-card major.',
      structure: '1NT - 2\u2663 (asking for majors)',
      responses: [
        '2\u2666 = No 4-card major',
        '2\u2665 = 4+ hearts (may also have 4 spades)',
        '2\u2660 = 4+ spades, denies 4 hearts',
      ],
      keyPoints: [
        'Need 8+ HCP (enough for game invitation)',
        'Must have at least one 4-card major',
        'With both majors, opener bids hearts first',
        'Don\'t use with 5-card major (use Jacoby Transfer instead)',
      ],
    },
    drillHands: [
      // Hands where Stayman SHOULD be used
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: '9', suit: 'D' }, { rank: '6', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '8', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you bid Stayman (2\u2663)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! You have 11 HCP and a 4-card spade suit. Stayman will help find a 4-4 spade fit.',
      },
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: '7', suit: 'D' }, { rank: '5', suit: 'D' },
          { rank: 'J', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you bid Stayman (2\u2663)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! You have 11 HCP and both 4-card majors. Stayman is perfect to find either fit.',
      },
      {
        hand: [
          { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: '8', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: 'K', suit: 'D' }, { rank: 'Q', suit: 'D' }, { rank: '7', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you bid Stayman (2\u2663)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! With 12 HCP and 4 spades, you have enough for game. Stayman first, then bid 3NT if no fit.',
      },
      // Hands where Stayman should NOT be used
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: '6', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: '9', suit: 'C' }, { rank: '5', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you bid Stayman (2\u2663)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! With a 5-card major, use Jacoby Transfer (2\u2665) instead of Stayman. This guarantees a fit.',
      },
      {
        hand: [
          { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '6', suit: 'S' },
          { rank: 'Q', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: 'K', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '4', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you bid Stayman (2\u2663)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You have no 4-card major. Just raise to 3NT with your 11 HCP.',
      },
      {
        hand: [
          { rank: '9', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' }, { rank: '2', suit: 'S' },
          { rank: 'J', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: 'Q', suit: 'D' }, { rank: '6', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'K', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you bid Stayman (2\u2663)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You only have 6 HCP. Pass and let partner play 1NT.',
      },
      // Follow-up question
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: 'J', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
          { bid: '2C', bidder: 'S', explanation: 'Stayman, asking for majors' },
          { bid: '2D', bidder: 'N', explanation: 'No 4-card major' },
        ],
        question: 'Partner denied a 4-card major. What do you bid now?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '3nt', label: '3NT' },
          { id: '2s', label: '2\u2660' },
          { id: '2h', label: '2\u2665' },
          { id: 'pass', label: 'Pass' },
        ],
        correctAnswer: '3nt',
        explanation: 'Bid 3NT. With 12 HCP, you have 27-29 combined. No major fit, so play game in notrump.',
      },
    ],
  },

  // ============================================
  // 2. JACOBY TRANSFERS
  // ============================================
  {
    id: 'jacoby_transfers',
    name: 'Jacoby Transfers',
    category: CONVENTION_CATEGORIES.RESPONSES,
    quickRef: {
      whenToUse: 'After partner opens 1NT, bid 2\u2666 with 5+ hearts or 2\u2665 with 5+ spades. Partner must complete the transfer.',
      structure: '1NT - 2\u2666 (transfer to hearts) / 1NT - 2\u2665 (transfer to spades)',
      responses: [
        '2\u2666 = 5+ hearts, any strength',
        '2\u2665 = 5+ spades, any strength',
        'Opener completes the transfer by bidding the major',
      ],
      keyPoints: [
        'Works with any strength (0-17+ HCP)',
        'Guarantees declaring in the major suit',
        'The NT opener becomes declarer, protecting honors',
        'After transfer, pass with weak hand, bid game with strong',
      ],
    },
    drillHands: [
      // Hands where Jacoby Transfer SHOULD be used
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: 'J', suit: 'D' }, { rank: '5', suit: 'D' },
          { rank: '8', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'What bid do you make?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '2h', label: '2\u2665' },
          { id: '2c', label: '2\u2663' },
          { id: '2s', label: '2\u2660' },
          { id: '3nt', label: '3NT' },
        ],
        correctAnswer: '2h',
        explanation: 'Bid 2\u2665, a Jacoby Transfer to spades. With 5 spades and 10 HCP, you want to play in spades with partner as declarer.',
      },
      {
        hand: [
          { rank: 'J', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: '8', suit: 'D' }, { rank: '5', suit: 'D' },
          { rank: '9', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'What bid do you make?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '2d', label: '2\u2666' },
          { id: '2c', label: '2\u2663' },
          { id: '2h', label: '2\u2665' },
          { id: '4h', label: '4\u2665' },
        ],
        correctAnswer: '2d',
        explanation: 'Bid 2\u2666, a Jacoby Transfer to hearts. With 5 hearts and 11 HCP, transfer first, then bid game.',
      },
      {
        hand: [
          { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' }, { rank: '2', suit: 'S' },
          { rank: 'Q', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '4', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: '7', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'K', suit: 'C' }, { rank: '9', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'What bid do you make?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '2d', label: '2\u2666' },
          { id: 'pass', label: 'Pass' },
          { id: '2c', label: '2\u2663' },
          { id: '2h', label: '2\u2665' },
        ],
        correctAnswer: '2d',
        explanation: 'Bid 2\u2666 to transfer to hearts. Even with only 5 HCP, a 6-card suit plays much better than 1NT.',
      },
      // Hands where transfer should NOT be used
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: '9', suit: 'D' }, { rank: '6', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '5', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you use a Jacoby Transfer?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! With 4-4 in the majors (not 5+ in either), use Stayman instead to find a fit.',
      },
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '6', suit: 'S' },
          { rank: 'Q', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: 'K', suit: 'C' }, { rank: '8', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you use a Jacoby Transfer?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You have no 5-card major. Just bid 3NT with your 13 HCP.',
      },
      {
        hand: [
          { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: 'K', suit: 'D' }, { rank: '8', suit: 'D' }, { rank: '5', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '7', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'What bid do you make?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '2h', label: '2\u2665' },
          { id: '4s', label: '4\u2660' },
          { id: '3s', label: '3\u2660' },
          { id: '2c', label: '2\u2663' },
        ],
        correctAnswer: '2h',
        explanation: 'Bid 2\u2665 to transfer to spades. With 10 HCP and 5 spades, transfer, then raise to game.',
      },
      // Follow-up question
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'Q', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' },
          { rank: 'J', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: '8', suit: 'C' }, { rank: '5', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
          { bid: '2H', bidder: 'S', explanation: 'Jacoby Transfer, 5+ spades' },
          { bid: '2S', bidder: 'N', explanation: 'Completing the transfer' },
        ],
        question: 'Partner completed the transfer. What do you bid now?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '4s', label: '4\u2660' },
          { id: '3s', label: '3\u2660' },
          { id: 'pass', label: 'Pass' },
          { id: '3nt', label: '3NT' },
        ],
        correctAnswer: '4s',
        explanation: 'Bid 4\u2660! With 11 HCP and a 5-card suit, you have 26-28 total. Game should make.',
      },
    ],
  },

  // ============================================
  // 3. TAKEOUT DOUBLES
  // ============================================
  {
    id: 'takeout_doubles',
    name: 'Takeout Doubles',
    category: CONVENTION_CATEGORIES.DOUBLES,
    quickRef: {
      whenToUse: 'After RHO opens at the 1 or 2 level, double with 12+ support points and shortness in opener\'s suit. You\'re asking partner to bid their best suit.',
      structure: '(1x) - X = "Pick a suit, partner!"',
      responses: [
        '0-8 HCP: Bid cheapest suit',
        '9-11 HCP: Jump in best suit',
        '12+ HCP: Cuebid or bid game',
        'With stopper in opener\'s suit: Bid NT',
      ],
      keyPoints: [
        'Shows 12+ support points (HCP + distribution)',
        'Shortness in opponent\'s suit (ideally 0-1)',
        'Support for all unbid suits, especially majors',
        'Partner MUST bid (unless intervening bid)',
      ],
    },
    drillHands: [
      // Hands where Takeout Double SHOULD be used
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'Q', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: '6', suit: 'D' },
          { rank: 'K', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1D', bidder: 'E', explanation: 'Opening bid' },
        ],
        question: 'Should you make a takeout double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! You have 13 HCP, shortness in diamonds, and support for all other suits. Classic takeout double.',
      },
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '8', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1C', bidder: 'E', explanation: 'Opening bid' },
        ],
        question: 'Should you make a takeout double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! With 15 HCP, 4-4 in the majors, and tolerance for diamonds, double is perfect.',
      },
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: 'J', suit: 'D' }, { rank: '4', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: 'K', suit: 'C' }, { rank: '7', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1D', bidder: 'E', explanation: 'Opening bid' },
        ],
        question: 'What action do you take?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: 'x', label: 'Double' },
          { id: '1s', label: '1\u2660' },
          { id: 'pass', label: 'Pass' },
          { id: '1nt', label: '1NT' },
        ],
        correctAnswer: 'x',
        explanation: 'Double! With 13 HCP and support for both majors plus clubs, this is a textbook takeout double.',
      },
      // Hands where Takeout Double should NOT be used
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' },
          { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' },
          { rank: 'K', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1H', bidder: 'E', explanation: 'Opening bid' },
        ],
        question: 'Should you make a takeout double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You have a 5-card spade suit. Overcall 1\u2660 instead of doubling.',
      },
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'J', suit: 'H' }, { rank: '8', suit: 'H' },
          { rank: 'Q', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '6', suit: 'D' }, { rank: '4', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '8', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1D', bidder: 'E', explanation: 'Opening bid' },
        ],
        question: 'Should you make a takeout double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You have 5 diamonds (their suit) and only 10 HCP. Pass and defend.',
      },
      {
        hand: [
          { rank: 'Q', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '4', suit: 'H' },
          { rank: 'J', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '6', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1S', bidder: 'E', explanation: 'Opening bid' },
        ],
        question: 'Should you make a takeout double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! Only 9 HCP is not enough for a takeout double. Pass.',
      },
      // Follow-up: Responding to partner's takeout double
      {
        hand: [
          { rank: 'Q', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: 'J', suit: 'D' }, { rank: '5', suit: 'D' },
          { rank: '8', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1D', bidder: 'E', explanation: 'Opening bid' },
          { bid: 'X', bidder: 'S', explanation: 'Takeout double' },
          { bid: 'Pass', bidder: 'W', explanation: '' },
        ],
        question: 'Partner made a takeout double. What do you bid?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '2h', label: '2\u2665' },
          { id: '1h', label: '1\u2665' },
          { id: '1s', label: '1\u2660' },
          { id: 'pass', label: 'Pass' },
        ],
        correctAnswer: '2h',
        explanation: 'Bid 2\u2665 (jump). You have 8 HCP and a 5-card heart suit. The jump shows 9-11 points.',
      },
    ],
  },

  // ============================================
  // 4. NEGATIVE DOUBLES
  // ============================================
  {
    id: 'negative_doubles',
    name: 'Negative Doubles',
    category: CONVENTION_CATEGORIES.DOUBLES,
    quickRef: {
      whenToUse: 'After partner opens and RHO overcalls, double to show the unbid major(s). Shows 6+ HCP at the 1-level, more at higher levels.',
      structure: '1\u2663 - (1\u2660) - X = "I have hearts!"',
      responses: [
        'At 1-level: Shows 4+ cards in unbid major(s), 6+ HCP',
        'At 2-level: Shows 4+ cards, 8+ HCP',
        'At 3-level: Shows 4+ cards, 10+ HCP',
      ],
      keyPoints: [
        'NOT for penalty - shows the unbid major(s)',
        'Guarantees 4 cards in unbid major (or both majors)',
        'Partner will bid with 4-card support, else rebid suit or NT',
        'Can\'t make a negative double without the unbid major',
      ],
    },
    drillHands: [
      // Hands where Negative Double SHOULD be used
      {
        hand: [
          { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '6', suit: 'H' },
          { rank: 'K', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: '9', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1D', bidder: 'N', explanation: 'Opening bid' },
          { bid: '1S', bidder: 'E', explanation: 'Overcall' },
        ],
        question: 'Should you make a negative double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! You have 10 HCP and 4 hearts (the unbid major). A negative double shows your hearts perfectly.',
      },
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: '9', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '5', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1C', bidder: 'N', explanation: 'Opening bid' },
          { bid: '1D', bidder: 'E', explanation: 'Overcall' },
        ],
        question: 'Should you make a negative double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! With 4-4 in the majors and 12 HCP, a negative double shows both majors at once.',
      },
      {
        hand: [
          { rank: '9', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: 'Q', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1C', bidder: 'N', explanation: 'Opening bid' },
          { bid: '1S', bidder: 'E', explanation: 'Overcall' },
        ],
        question: 'What action do you take?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: 'x', label: 'Double' },
          { id: '2h', label: '2\u2665' },
          { id: '1nt', label: '1NT' },
          { id: 'pass', label: 'Pass' },
        ],
        correctAnswer: 'x',
        explanation: 'Double (negative). You have 4 hearts and 10 HCP. A negative double is better than 2\u2665 which would show 5+ hearts.',
      },
      // Hands where Negative Double should NOT be used
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' },
          { rank: 'J', suit: 'D' }, { rank: '5', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: '9', suit: 'C' }, { rank: '6', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1C', bidder: 'N', explanation: 'Opening bid' },
          { bid: '1H', bidder: 'E', explanation: 'Overcall' },
        ],
        question: 'Should you make a negative double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! With 5 spades, bid 1\u2660 directly. Negative double would show only 4 spades.',
      },
      {
        hand: [
          { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: '9', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: 'Q', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: 'K', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1D', bidder: 'N', explanation: 'Opening bid' },
          { bid: '1S', bidder: 'E', explanation: 'Overcall' },
        ],
        question: 'Should you make a negative double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You only have 3 hearts. A negative double promises 4. Bid 1NT or support diamonds.',
      },
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' },
          { rank: 'Q', suit: 'D' }, { rank: '9', suit: 'D' }, { rank: '6', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '8', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1C', bidder: 'N', explanation: 'Opening bid' },
          { bid: '1H', bidder: 'E', explanation: 'Overcall' },
        ],
        question: 'What action do you take?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '1s', label: '1\u2660' },
          { id: 'x', label: 'Double' },
          { id: '2c', label: '2\u2663' },
          { id: '1nt', label: '1NT' },
        ],
        correctAnswer: '1s',
        explanation: 'Bid 1\u2660. With 4 spades and no hearts, don\'t use negative double (which shows hearts after 1\u2665 overcall).',
      },
      // Follow-up question
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '6', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: '7', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'J', suit: 'C' }, { rank: '4', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1D', bidder: 'N', explanation: 'Opening bid' },
          { bid: '2C', bidder: 'E', explanation: 'Overcall' },
        ],
        question: 'Should you make a negative double?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! You have both majors and 11 HCP (enough for a 2-level negative double). Double shows both majors.',
      },
    ],
  },

  // ============================================
  // 5. BLACKWOOD / RKC
  // ============================================
  {
    id: 'blackwood',
    name: 'Blackwood (4NT)',
    category: CONVENTION_CATEGORIES.SLAM,
    quickRef: {
      whenToUse: 'When you have agreed on a trump suit and want to check for aces (or key cards) before bidding slam. Need 33+ combined HCP for small slam.',
      structure: '4NT asks for aces/key cards',
      responses: [
        'Standard Blackwood: 5\u2663=0/4, 5\u2666=1, 5\u2665=2, 5\u2660=3',
        'RKC 1430: 5\u2663=1/4, 5\u2666=0/3, 5\u2665=2 no Q, 5\u2660=2+Q',
        '5NT asks for kings (guarantees all aces)',
      ],
      keyPoints: [
        'Only use when you have a trump fit established',
        'Don\'t use with a void (cue-bid instead)',
        'Missing 2 aces = stop at 5-level',
        'Missing 1 ace = bid small slam (6)',
        'Have all aces = consider grand slam (7)',
      ],
    },
    drillHands: [
      // Hands where Blackwood SHOULD be used
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: 'K', suit: 'D' }, { rank: '7', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1S', bidder: 'N', explanation: 'Opening bid' },
          { bid: '3S', bidder: 'S', explanation: 'Limit raise, 4+ spades, 10-12 points' },
          { bid: '4D', bidder: 'N', explanation: 'Cue-bid, slam interest' },
        ],
        question: 'Should you bid 4NT (Blackwood)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! You have 17 HCP, partner shows 10-12. That\'s 27-29 with a fit. Check for aces before slam.',
      },
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '8', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '3', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '6', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1S', bidder: 'S', explanation: 'Opening bid' },
          { bid: '2NT', bidder: 'N', explanation: 'Jacoby 2NT, 4+ spades, game-forcing' },
          { bid: '3D', bidder: 'S', explanation: 'Singleton/void in diamonds' },
          { bid: '4S', bidder: 'N', explanation: 'Signing off in game' },
        ],
        question: 'Should you bid 4NT (Blackwood)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! Partner\'s Jacoby 2NT shows 13+ HCP. You have 18. Check for aces - slam is likely.',
      },
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '8', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'K', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '5', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: '7', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1H', bidder: 'S', explanation: 'Opening bid' },
          { bid: '3H', bidder: 'N', explanation: 'Limit raise, 4+ hearts, 10-12 points' },
        ],
        question: 'What do you bid?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '4nt', label: '4NT' },
          { id: '4h', label: '4\u2665' },
          { id: '4d', label: '4\u2666' },
          { id: '3s', label: '3\u2660' },
        ],
        correctAnswer: '4nt',
        explanation: 'Bid 4NT (Blackwood). With 18 HCP and partner showing 10-12, you have 28-30 total. Check for aces!',
      },
      // Hands where Blackwood should NOT be used
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: 'A', suit: 'C' }, { rank: '9', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1S', bidder: 'S', explanation: 'Opening bid' },
          { bid: '4S', bidder: 'N', explanation: 'Preemptive raise' },
        ],
        question: 'Should you bid 4NT (Blackwood)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You have a VOID in diamonds. Use cue-bids instead of Blackwood when you have a void.',
      },
      {
        hand: [
          { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '6', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '5', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1H', bidder: 'N', explanation: 'Opening bid' },
          { bid: '2H', bidder: 'S', explanation: 'Single raise, 6-10 points' },
        ],
        question: 'Should you bid 4NT (Blackwood)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! With only 10 HCP and partner opening 12-15, you don\'t have enough for slam (22-25 total). Just bid 4\u2665.',
      },
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '8', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '6', suit: 'H' },
          { rank: '7', suit: 'D' }, { rank: '5', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: 'K', suit: 'C' }, { rank: 'Q', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1NT', bidder: 'N', explanation: '15-17 HCP, balanced' },
        ],
        question: 'Should you bid 4NT (Blackwood)?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! After 1NT, 4NT is QUANTITATIVE (inviting 6NT), not Blackwood. You need to transfer or use Stayman first if you want to use Blackwood.',
      },
      // Follow-up after Blackwood response
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '5', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '4', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '7', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '3', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '1S', bidder: 'S', explanation: 'Opening bid' },
          { bid: '3S', bidder: 'N', explanation: 'Limit raise' },
          { bid: '4NT', bidder: 'S', explanation: 'Blackwood' },
          { bid: '5D', bidder: 'N', explanation: '1 ace' },
        ],
        question: 'Partner showed 1 ace. What do you bid?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '6s', label: '6\u2660' },
          { id: '5s', label: '5\u2660' },
          { id: '5nt', label: '5NT' },
          { id: '7s', label: '7\u2660' },
        ],
        correctAnswer: '6s',
        explanation: 'Bid 6\u2660. You have 3 aces, partner has 1. That\'s all 4 aces. Small slam is safe!',
      },
    ],
  },

  // ============================================
  // 6. WEAK TWO BIDS
  // ============================================
  {
    id: 'weak_two',
    name: 'Weak Two Bids',
    category: CONVENTION_CATEGORIES.CONSTRUCTIVE,
    quickRef: {
      whenToUse: 'Open 2\u2666, 2\u2665, or 2\u2660 with a 6-card suit and 5-10 HCP. This is a preemptive opening showing a weak hand with a long suit.',
      structure: '2\u2666/2\u2665/2\u2660 = 6+ cards, 5-10 HCP',
      responses: [
        '2NT = Feature ask (forcing)',
        'Raise to 3 = Competitive/blocking',
        'Raise to 4 = To make or further preempt',
        'New suit = Natural, forcing',
      ],
      keyPoints: [
        'Need a good 6-card suit (2 of top 5 honors)',
        '5-10 HCP (11+ should open at 1-level)',
        'Don\'t open weak 2 with a 4-card major on side',
        'Vulnerability matters - be sound when vulnerable',
      ],
    },
    drillHands: [
      // Hands where Weak Two SHOULD be used
      {
        hand: [
          { rank: '7', suit: 'S' }, { rank: '4', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '6', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: '8', suit: 'D' }, { rank: '5', suit: 'D' }, { rank: '2', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [],
        question: 'What do you open?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '2h', label: '2\u2665' },
          { id: '1h', label: '1\u2665' },
          { id: 'pass', label: 'Pass' },
          { id: '3h', label: '3\u2665' },
        ],
        correctAnswer: '2h',
        explanation: 'Open 2\u2665. You have a good 6-card heart suit (KQJ) and 8 HCP. Classic weak two.',
      },
      {
        hand: [
          { rank: 'Q', suit: 'S' }, { rank: 'J', suit: 'S' }, { rank: '10', suit: 'S' }, { rank: '8', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: '9', suit: 'H' }, { rank: '5', suit: 'H' },
          { rank: 'K', suit: 'D' }, { rank: '7', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: '8', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [],
        question: 'Should you open a weak two?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'yes',
        explanation: 'Yes! Open 2\u2660. You have 6 spades with QJ10 (good suit quality) and 7 HCP.',
      },
      {
        hand: [
          { rank: '5', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '5', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: 'Q', suit: 'D' }, { rank: '8', suit: 'D' }, { rank: '6', suit: 'D' },
          { rank: '9', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [],
        question: 'What do you open?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '2h', label: '2\u2665' },
          { id: '1h', label: '1\u2665' },
          { id: 'pass', label: 'Pass' },
          { id: '3h', label: '3\u2665' },
        ],
        correctAnswer: '2h',
        explanation: 'Open 2\u2665. Six hearts headed by the AJ, 7 HCP. Good weak two.',
      },
      // Hands where Weak Two should NOT be used
      {
        hand: [
          { rank: 'K', suit: 'S' }, { rank: 'Q', suit: 'S' }, { rank: '9', suit: 'S' }, { rank: '6', suit: 'S' },
          { rank: 'A', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '8', suit: 'H' }, { rank: '5', suit: 'H' }, { rank: '3', suit: 'H' }, { rank: '2', suit: 'H' },
          { rank: '7', suit: 'D' }, { rank: '4', suit: 'D' },
          { rank: '8', suit: 'C' },
        ],
        auctionSoFar: [],
        question: 'Should you open a weak two?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You have a 4-card spade side suit. Open 1\u2665 instead - a weak two denies a 4-card major on the side.',
      },
      {
        hand: [
          { rank: 'J', suit: 'S' }, { rank: '6', suit: 'S' }, { rank: '3', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '9', suit: 'H' }, { rank: '7', suit: 'H' }, { rank: '4', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: '8', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '5', suit: 'C' },
        ],
        auctionSoFar: [],
        question: 'Should you open a weak two?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You have 12 HCP. That\'s too strong for a weak two. Open 1\u2665.',
      },
      {
        hand: [
          { rank: '9', suit: 'S' }, { rank: '7', suit: 'S' }, { rank: '5', suit: 'S' }, { rank: '4', suit: 'S' }, { rank: '2', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'J', suit: 'H' }, { rank: '3', suit: 'H' },
          { rank: 'Q', suit: 'D' }, { rank: '8', suit: 'D' }, { rank: '6', suit: 'D' },
          { rank: 'A', suit: 'C' }, { rank: '4', suit: 'C' },
        ],
        auctionSoFar: [],
        question: 'Should you open a weak two?',
        questionType: QUESTION_TYPES.YES_NO,
        correctAnswer: 'no',
        explanation: 'No! You only have 5 spades, not 6. A weak two requires a 6-card suit. Pass or consider opening light at 1\u2660.',
      },
      // Follow-up: Responding to partner's weak two
      {
        hand: [
          { rank: 'A', suit: 'S' }, { rank: 'K', suit: 'S' }, { rank: '8', suit: 'S' },
          { rank: 'K', suit: 'H' }, { rank: 'Q', suit: 'H' }, { rank: '9', suit: 'H' },
          { rank: 'A', suit: 'D' }, { rank: 'J', suit: 'D' }, { rank: '5', suit: 'D' },
          { rank: 'Q', suit: 'C' }, { rank: '7', suit: 'C' }, { rank: '3', suit: 'C' }, { rank: '2', suit: 'C' },
        ],
        auctionSoFar: [
          { bid: '2H', bidder: 'N', explanation: 'Weak two, 6+ hearts, 5-10 HCP' },
        ],
        question: 'Partner opened 2\u2665. What do you bid?',
        questionType: QUESTION_TYPES.BID_CHOICE,
        choices: [
          { id: '4h', label: '4\u2665' },
          { id: '2nt', label: '2NT' },
          { id: '3h', label: '3\u2665' },
          { id: '3nt', label: '3NT' },
        ],
        correctAnswer: '4h',
        explanation: 'Bid 4\u2665. With 18 HCP and 3-card heart support, game is likely to make. Partner has 5-10, giving 23-28 total.',
      },
    ],
  },
];

/**
 * Get a convention by ID
 * @param {string} id - Convention ID
 * @returns {Object|undefined} Convention data or undefined
 */
export const getConventionById = (id) => {
  return CONVENTIONS.find(conv => conv.id === id);
};

/**
 * Get all conventions in a category
 * @param {string} category - Convention category
 * @returns {Array} Conventions in that category
 */
export const getConventionsByCategory = (category) => {
  return CONVENTIONS.filter(conv => conv.category === category);
};

/**
 * Get drill hand by convention ID and index
 * @param {string} conventionId - Convention ID
 * @param {number} handIndex - Index of the drill hand
 * @returns {Object|undefined} Drill hand data or undefined
 */
export const getDrillHand = (conventionId, handIndex) => {
  const convention = getConventionById(conventionId);
  if (!convention) return undefined;
  return convention.drillHands[handIndex];
};

export default CONVENTIONS;
