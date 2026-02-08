/**
 * Mock Data for Critical Trick Flow
 * 5 declarer play problems testing key techniques
 */

/**
 * @typedef {Object} Plan
 * @property {string} id - Unique identifier
 * @property {string} label - Display text with suit symbols
 * @property {boolean} isCorrect - Whether this is the optimal plan
 * @property {string} explanation - Why this plan is right/wrong
 * @property {string} technique - The technique category
 */

/**
 * @typedef {Object} CriticalTrickProblem
 * @property {string} id - Unique problem identifier
 * @property {string} contract - Contract string like "4S" or "3NT"
 * @property {string} vulnerability - "None" | "NS" | "EW" | "Both"
 * @property {Array<{rank: string, suit: string}>} dummyHand - Dummy's remaining cards
 * @property {Array<{rank: string, suit: string}>} declarerHand - Declarer's remaining cards
 * @property {{ns: number, ew: number}} tricksSoFar - Tricks won by each side
 * @property {number} tricksNeeded - Tricks declarer needs to make contract
 * @property {string} situationText - Description of the situation
 * @property {Plan[]} plans - Array of 3-4 plan options
 * @property {string} technique - Primary technique being tested
 */

export const CRITICAL_TRICK_PROBLEMS = [
  // Problem 1: Finesse vs Drop
  {
    id: 'finesse-vs-drop-1',
    contract: '4S',
    vulnerability: 'None',
    dummyHand: [
      { rank: 'A', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: '6', suit: 'C' },
      { rank: '5', suit: 'C' },
    ],
    declarerHand: [
      { rank: 'K', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: '7', suit: 'D' },
      { rank: '4', suit: 'D' },
      { rank: 'A', suit: 'C' },
    ],
    tricksSoFar: { ns: 3, ew: 1 },
    tricksNeeded: 7,
    situationText: 'You have 9 trumps missing the 9, 8, 7, 6. West has shown out on a previous heart lead, suggesting length in the minors. How do you play the trump suit to avoid a loser?',
    plans: [
      {
        id: 'plan-finesse',
        label: 'Lead low to the Queen, finessing against East',
        isCorrect: true,
        explanation: 'With 9 trumps missing 4, the finesse (50%) beats playing for the drop (approximately 48%). Additionally, West showing minor suit length suggests East is more likely to have trump length.',
        technique: 'Finesse'
      },
      {
        id: 'plan-drop',
        label: 'Cash the Ace and King, playing for the drop',
        isCorrect: false,
        explanation: 'With 9 trumps, the drop percentage (48%) is slightly lower than the finesse (50%). The inference from West\'s shape makes the finesse clearly correct.',
        technique: 'Drop Play'
      },
      {
        id: 'plan-low-to-king',
        label: 'Lead low to the King first',
        isCorrect: false,
        explanation: 'Starting with the King gains nothing and could cost if East has a singleton honor. The standard play is to finesse toward the AQ combination.',
        technique: 'Finesse'
      }
    ],
    technique: 'Finesse vs Drop'
  },

  // Problem 2: Hold-up Play
  {
    id: 'holdup-play-1',
    contract: '3NT',
    vulnerability: 'NS',
    dummyHand: [
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '5', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: 'J', suit: 'D' },
      { rank: '7', suit: 'C' },
    ],
    declarerHand: [
      { rank: 'A', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: '10', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: 'Q', suit: 'C' },
      { rank: '3', suit: 'C' },
    ],
    tricksSoFar: { ns: 0, ew: 0 },
    tricksNeeded: 9,
    situationText: 'West leads the 4 of hearts. East plays the King. You have 6 diamond tricks, 3 spade tricks, and the heart Ace. But you need to take a club finesse which might lose to West.',
    plans: [
      {
        id: 'plan-duck-twice',
        label: 'Duck the first two hearts, win the third',
        isCorrect: true,
        explanation: 'By holding up twice, you exhaust East of hearts. If the club finesse loses to West, he may have no hearts left to lead. This is the classic hold-up play in 3NT.',
        technique: 'Hold-up'
      },
      {
        id: 'plan-win-immediately',
        label: 'Win the Ace immediately and take the club finesse',
        isCorrect: false,
        explanation: 'If you win immediately and the club finesse loses, West can cash enough hearts to defeat the contract. The hold-up is essential.',
        technique: 'None'
      },
      {
        id: 'plan-duck-once',
        label: 'Duck once, then win the second round',
        isCorrect: false,
        explanation: 'Ducking only once may not be enough. If hearts are 5-3, East will still have a heart to lead when West wins the club. Duck twice to be safe.',
        technique: 'Hold-up'
      }
    ],
    technique: 'Hold-up Play'
  },

  // Problem 3: Trump Management
  {
    id: 'trump-management-1',
    contract: '4H',
    vulnerability: 'EW',
    dummyHand: [
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: '8', suit: 'C' },
      { rank: '7', suit: 'C' },
    ],
    declarerHand: [
      { rank: 'A', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '6', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: 'K', suit: 'C' },
      { rank: 'Q', suit: 'C' },
    ],
    tricksSoFar: { ns: 1, ew: 0 },
    tricksNeeded: 9,
    situationText: 'You won the opening diamond lead in dummy. You have 4 spade tricks, 5 trump tricks, and the diamond Ace already cashed. But clubs are a potential loser, and you need to ruff diamonds in hand.',
    plans: [
      {
        id: 'plan-ruff-first',
        label: 'Ruff diamonds in hand before drawing trumps',
        isCorrect: true,
        explanation: 'You need to ruff diamonds in hand while dummy still has trumps. Draw trumps later. If you draw trumps first, you won\'t be able to use your small trumps productively.',
        technique: 'Trump Management'
      },
      {
        id: 'plan-draw-all-trumps',
        label: 'Draw all trumps immediately, then run spades',
        isCorrect: false,
        explanation: 'Drawing all trumps eliminates the chance to ruff in hand. You\'d need all your side-suit tricks to run without a club loser, which isn\'t guaranteed.',
        technique: 'Draw Trumps'
      },
      {
        id: 'plan-draw-two-trumps',
        label: 'Draw exactly two rounds of trumps, then ruff',
        isCorrect: false,
        explanation: 'Two rounds might not be enough if trumps are 4-2. The key insight is to ruff first while you still have trump control in both hands.',
        technique: 'Trump Management'
      }
    ],
    technique: 'Trump Management'
  },

  // Problem 4: Endplay
  {
    id: 'endplay-1',
    contract: '4S',
    vulnerability: 'Both',
    dummyHand: [
      { rank: 'Q', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: '7', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: '8', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '6', suit: 'C' },
    ],
    declarerHand: [
      { rank: 'A', suit: 'S' },
      { rank: 'K', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: 'K', suit: 'C' },
    ],
    tricksSoFar: { ns: 7, ew: 2 },
    tricksNeeded: 3,
    situationText: 'You need 3 more tricks. You have stripped hearts and diamonds. West is known to hold the remaining trumps and clubs. You are in dummy with the club suit unplayed.',
    plans: [
      {
        id: 'plan-endplay',
        label: 'Exit with a club, forcing West to lead into your tenace or give a ruff-sluff',
        isCorrect: true,
        explanation: 'The classic endplay! After stripping, exit to West. He must either lead a club into your AK or give a ruff-sluff. Either way, you make your contract.',
        technique: 'Endplay'
      },
      {
        id: 'plan-finesse-clubs',
        label: 'Lead a club to the King, hoping East has the Queen',
        isCorrect: false,
        explanation: 'You\'ve established West has the clubs. A finesse through West fails. The endplay guarantees the contract instead of relying on a 50% finesse.',
        technique: 'Finesse'
      },
      {
        id: 'plan-cash-out',
        label: 'Cash the Ace-King of clubs and hope the Queen drops',
        isCorrect: false,
        explanation: 'The Queen won\'t drop from West who has club length. The endplay is 100% here; playing for the drop is unnecessary risk.',
        technique: 'Drop Play'
      },
      {
        id: 'plan-draw-trumps',
        label: 'Draw the remaining trumps first',
        isCorrect: false,
        explanation: 'Drawing trumps removes your ruff-sluff threat. Keep trumps in both hands to maximize pressure on West.',
        technique: 'Trump Management'
      }
    ],
    technique: 'Endplay'
  },

  // Problem 5: Counting
  {
    id: 'counting-1',
    contract: '6NT',
    vulnerability: 'None',
    dummyHand: [
      { rank: 'A', suit: 'S' },
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: 'J', suit: 'C' },
    ],
    declarerHand: [
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: 'J', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: 'A', suit: 'C' },
      { rank: 'K', suit: 'C' },
      { rank: 'Q', suit: 'C' },
    ],
    tricksSoFar: { ns: 8, ew: 0 },
    tricksNeeded: 4,
    situationText: 'You\'ve cashed 8 tricks. West started with 5 hearts (bid 2H) and has followed to 3 spades and 2 diamonds. You need the club Queen to drop for your 12th trick. Where is it?',
    plans: [
      {
        id: 'plan-play-for-drop',
        label: 'Cash Ace-King of clubs, playing for the drop from West',
        isCorrect: true,
        explanation: 'West started with 5 hearts, 3 spades, 2 diamonds = 10 cards. That leaves exactly 3 clubs. East has only 2 clubs. The Queen is more likely with West (3 vs 2).',
        technique: 'Counting'
      },
      {
        id: 'plan-finesse-east',
        label: 'Lead the Jack of clubs, finessing against East',
        isCorrect: false,
        explanation: 'The count tells you West has more clubs. With West having 3 clubs and East having 2, the Queen is 60% to be with West. Play for the drop.',
        technique: 'Finesse'
      },
      {
        id: 'plan-guess',
        label: 'Lead toward the Ace-King and guess based on tempo',
        isCorrect: false,
        explanation: 'You don\'t need to guess. The bidding and play have revealed the distribution. Use the count to make the mathematically correct play.',
        technique: 'None'
      }
    ],
    technique: 'Counting'
  }
];

/**
 * Get a random critical trick problem
 * @returns {CriticalTrickProblem}
 */
export const getRandomProblem = () => {
  const index = Math.floor(Math.random() * CRITICAL_TRICK_PROBLEMS.length);
  return CRITICAL_TRICK_PROBLEMS[index];
};

/**
 * Get problem by ID
 * @param {string} id
 * @returns {CriticalTrickProblem | undefined}
 */
export const getProblemById = (id) => {
  return CRITICAL_TRICK_PROBLEMS.find(p => p.id === id);
};

/**
 * Get all problem IDs
 * @returns {string[]}
 */
export const getAllProblemIds = () => {
  return CRITICAL_TRICK_PROBLEMS.map(p => p.id);
};

export default CRITICAL_TRICK_PROBLEMS;
