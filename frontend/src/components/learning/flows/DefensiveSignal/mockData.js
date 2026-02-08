/**
 * Defensive Signal Quiz - Mock Data
 * 8 pre-built situations covering Attitude, Count, and Suit Preference signals
 *
 * Signal Types:
 * - attitude: High = encourage, Low = discourage
 * - count: High-low = even count, Low-high = odd count
 * - suitPreference: High = prefer higher suit, Low = prefer lower suit
 */

/**
 * @typedef {'attitude' | 'count' | 'suitPreference'} SignalType
 */

/**
 * @typedef {Object} SignalSituation
 * @property {string} id - Unique identifier
 * @property {SignalType} signalType - Type of signal expected
 * @property {string} contract - Contract being played (e.g., "4S")
 * @property {string} declarerPosition - Who is declarer (N, E, S, W)
 * @property {string} partnerLead - Card partner led (e.g., "HA" for Ace of Hearts)
 * @property {string} signalSuit - Suit to signal in (S, H, D, C)
 * @property {Array<{rank: string, suit: string}>} yourHand - Your 13 cards
 * @property {Array<{rank: string, suit: string}>} dummy - Dummy's cards
 * @property {string} correctCard - The correct card to play (e.g., "K" for king)
 * @property {string} explanation - Why this is the correct signal
 * @property {string} prompt - The question to ask the player
 */

export const SIGNAL_SITUATIONS = [
  // ============ ATTITUDE SIGNALS (1-3) ============
  {
    id: 'attitude-1',
    signalType: 'attitude',
    level: 1,
    contract: '4S',
    declarerPosition: 'S',
    partnerLead: 'HA',
    signalSuit: 'H',
    yourHand: [
      { rank: '8', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: 'J', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: '7', suit: 'C' },
      { rank: '3', suit: 'C' },
      { rank: 'Q', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: '5', suit: 'D' },
    ],
    dummy: [
      { rank: 'K', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: 'A', suit: 'C' },
      { rank: 'K', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '10', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '2', suit: 'D' },
    ],
    correctCard: 'K',
    explanation: 'Play the King to ENCOURAGE a heart continuation. You want partner to lead hearts again so you can win with the King.',
    prompt: 'Partner leads the Ace of Hearts. Which heart do you play?',
  },
  {
    id: 'attitude-2',
    signalType: 'attitude',
    level: 1,
    contract: '3NT',
    declarerPosition: 'S',
    partnerLead: 'DK',
    signalSuit: 'D',
    yourHand: [
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: '9', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: '10', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: '4', suit: 'C' },
      { rank: '9', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '3', suit: 'D' },
    ],
    dummy: [
      { rank: 'A', suit: 'S' },
      { rank: 'K', suit: 'S' },
      { rank: '8', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: 'A', suit: 'C' },
      { rank: 'Q', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: 'J', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: '2', suit: 'D' },
    ],
    correctCard: '3',
    explanation: 'Play the 3 to DISCOURAGE diamonds. You have no useful diamond honor and partner should look elsewhere for tricks.',
    prompt: 'Partner leads the King of Diamonds. Which diamond do you play?',
  },
  {
    id: 'attitude-3',
    signalType: 'attitude',
    level: 1,
    contract: '4H',
    declarerPosition: 'S',
    partnerLead: 'SA',
    signalSuit: 'S',
    yourHand: [
      { rank: 'Q', suit: 'S' },
      { rank: '9', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '10', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: 'K', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: '2', suit: 'C' },
      { rank: 'A', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '4', suit: 'D' },
    ],
    dummy: [
      { rank: 'K', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '4', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: 'Q', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: '5', suit: 'C' },
      { rank: 'Q', suit: 'D' },
      { rank: 'J', suit: 'D' },
      { rank: '6', suit: 'D' },
    ],
    correctCard: 'Q',
    explanation: 'Play the Queen to ENCOURAGE spades. You have the Queen and want partner to continue the suit so you can promote your honor.',
    prompt: 'Partner leads the Ace of Spades. Which spade do you play?',
  },

  // ============ COUNT SIGNALS (4-5) ============
  {
    id: 'count-1',
    signalType: 'count',
    level: 2,
    contract: '3NT',
    declarerPosition: 'S',
    partnerLead: 'H5',
    signalSuit: 'H',
    yourHand: [
      { rank: 'J', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '8', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: 'Q', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '2', suit: 'C' },
      { rank: 'J', suit: 'D' },
      { rank: '9', suit: 'D' },
      { rank: '5', suit: 'D' },
    ],
    dummy: [
      { rank: 'Q', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: '2', suit: 'H' },
      { rank: 'A', suit: 'C' },
      { rank: 'K', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '3', suit: 'D' },
    ],
    correctCard: 'K',
    explanation: 'Play the King (high) to show EVEN count. With 4 hearts, start high-low to tell partner you have an even number.',
    prompt: 'Declarer leads the Ace from dummy. Which heart do you signal with?',
  },
  {
    id: 'count-2',
    signalType: 'count',
    level: 2,
    contract: '4S',
    declarerPosition: 'S',
    partnerLead: 'CK',
    signalSuit: 'C',
    yourHand: [
      { rank: '8', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: 'Q', suit: 'H' },
      { rank: '9', suit: 'H' },
      { rank: '7', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: 'J', suit: 'C' },
      { rank: '5', suit: 'C' },
      { rank: '3', suit: 'C' },
      { rank: 'A', suit: 'D' },
      { rank: '10', suit: 'D' },
      { rank: '4', suit: 'D' },
    ],
    dummy: [
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '9', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: 'Q', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '2', suit: 'D' },
    ],
    correctCard: '3',
    explanation: 'Play the 3 (low) to show ODD count. With 3 clubs, start low-high to tell partner you have an odd number.',
    prompt: 'Partner leads the King of Clubs. Which club do you play?',
  },

  // ============ SUIT PREFERENCE SIGNALS (6-8) ============
  {
    id: 'suitpref-1',
    signalType: 'suitPreference',
    level: 3,
    contract: '4H',
    declarerPosition: 'S',
    partnerLead: 'CA',
    signalSuit: 'C',
    yourHand: [
      { rank: 'A', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '8', suit: 'S' },
      { rank: '3', suit: 'S' },
      { rank: '7', suit: 'H' },
      { rank: '4', suit: 'H' },
      { rank: '9', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: '2', suit: 'C' },
      { rank: 'J', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: '5', suit: 'D' },
      { rank: '3', suit: 'D' },
    ],
    dummy: [
      { rank: 'K', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: 'K', suit: 'C' },
      { rank: 'Q', suit: 'C' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '2', suit: 'D' },
    ],
    correctCard: '9',
    explanation: 'Play the 9 (high club) to show SPADE preference. Partner will give you a ruff in clubs, then you want a spade return.',
    prompt: 'Partner leads the Ace of Clubs (singleton in dummy). Which club signals spade preference?',
  },
  {
    id: 'suitpref-2',
    signalType: 'suitPreference',
    level: 3,
    contract: '4S',
    declarerPosition: 'S',
    partnerLead: 'DA',
    signalSuit: 'D',
    yourHand: [
      { rank: '9', suit: 'S' },
      { rank: '7', suit: 'S' },
      { rank: '5', suit: 'S' },
      { rank: 'K', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: '10', suit: 'H' },
      { rank: '6', suit: 'H' },
      { rank: 'J', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: '4', suit: 'C' },
      { rank: '9', suit: 'D' },
      { rank: '6', suit: 'D' },
      { rank: '3', suit: 'D' },
    ],
    dummy: [
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: 'J', suit: 'S' },
      { rank: '10', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: 'A', suit: 'C' },
      { rank: 'K', suit: 'C' },
      { rank: '6', suit: 'C' },
      { rank: 'K', suit: 'D' },
      { rank: '8', suit: 'D' },
      { rank: '2', suit: 'D' },
    ],
    correctCard: '9',
    explanation: 'Play the 9 (high diamond) to show HEART preference. Between hearts and clubs (the other two side suits), hearts is the higher ranking suit.',
    prompt: 'Partner leads the Ace of Diamonds. Which diamond signals heart preference?',
  },
  {
    id: 'suitpref-3',
    signalType: 'suitPreference',
    level: 3,
    contract: '4H',
    declarerPosition: 'S',
    partnerLead: 'SA',
    signalSuit: 'S',
    yourHand: [
      { rank: '10', suit: 'S' },
      { rank: '6', suit: 'S' },
      { rank: '2', suit: 'S' },
      { rank: '9', suit: 'H' },
      { rank: '5', suit: 'H' },
      { rank: '3', suit: 'H' },
      { rank: 'A', suit: 'C' },
      { rank: 'Q', suit: 'C' },
      { rank: 'J', suit: 'C' },
      { rank: '8', suit: 'C' },
      { rank: '9', suit: 'D' },
      { rank: '7', suit: 'D' },
      { rank: '4', suit: 'D' },
    ],
    dummy: [
      { rank: 'K', suit: 'S' },
      { rank: 'Q', suit: 'S' },
      { rank: '8', suit: 'S' },
      { rank: 'A', suit: 'H' },
      { rank: 'K', suit: 'H' },
      { rank: 'Q', suit: 'H' },
      { rank: 'J', suit: 'H' },
      { rank: 'K', suit: 'C' },
      { rank: '9', suit: 'C' },
      { rank: 'A', suit: 'D' },
      { rank: 'K', suit: 'D' },
      { rank: 'Q', suit: 'D' },
      { rank: '2', suit: 'D' },
    ],
    correctCard: '2',
    explanation: 'Play the 2 (lowest spade) to show CLUB preference. Between diamonds and clubs (the side suits), clubs is the lower ranking suit.',
    prompt: 'Partner leads the Ace of Spades. Which spade signals club preference?',
  },
];

/**
 * Get situations filtered by signal type
 * @param {SignalType} type
 * @returns {SignalSituation[]}
 */
export const getSituationsByType = (type) => {
  return SIGNAL_SITUATIONS.filter((s) => s.signalType === type);
};

/**
 * Get situations for a specific level
 * @param {number} level - 1=Attitude, 2=Count, 3=Suit Preference
 * @returns {SignalSituation[]}
 */
export const getSituationsByLevel = (level) => {
  return SIGNAL_SITUATIONS.filter((s) => s.level === level);
};

/**
 * Get all situations shuffled
 * @returns {SignalSituation[]}
 */
export const getShuffledSituations = () => {
  const shuffled = [...SIGNAL_SITUATIONS];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

export default SIGNAL_SITUATIONS;
