/**
 * DailyHand.logic.js
 *
 * State machine and scoring logic for the Daily Hand Challenge flow.
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

// Flow states for Daily Hand
export const FLOW_STATES = {
  DEAL: 'DEAL',
  BID: 'BID',
  PLAY: 'PLAY',
  RESULT: 'RESULT',
  SUMMARY: 'SUMMARY',
};

// Bidding level constants
export const BID_LEVELS = [1, 2, 3, 4, 5, 6, 7];

// Strain order (for bidding box)
export const STRAINS = ['C', 'D', 'H', 'S', 'NT'];

// Strain display symbols
export const STRAIN_SYMBOLS = {
  C: '\u2663', // clubs
  D: '\u2666', // diamonds
  H: '\u2665', // hearts
  S: '\u2660', // spades
  NT: 'NT',
};

/**
 * Local storage key for daily hand data
 */
const DAILY_STORAGE_KEY = 'daily_hand_challenge';

/**
 * Get today's date string in YYYY-MM-DD format
 * @returns {string}
 */
export const getTodayString = () => {
  const now = new Date();
  return now.toISOString().split('T')[0];
};

/**
 * Seeded random number generator for deterministic hands per day
 * Uses a simple LCG algorithm
 *
 * @param {string} seed - The seed string (typically today's date)
 * @returns {function(): number} - Returns a function that produces random numbers [0, 1)
 */
export const createSeededRandom = (seed) => {
  // Simple hash function to convert string to number
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    const char = seed.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }

  // LCG parameters (same as glibc)
  const a = 1103515245;
  const c = 12345;
  const m = 2 ** 31;

  let state = Math.abs(hash);

  return () => {
    state = (a * state + c) % m;
    return state / m;
  };
};

/**
 * Fisher-Yates shuffle with seeded random
 * @param {Array} array - Array to shuffle
 * @param {function(): number} random - Seeded random function
 * @returns {Array} - Shuffled array (mutates original)
 */
const shuffleArray = (array, random) => {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
};

/**
 * Generate a deterministic hand for a given date
 * Same date always produces the same hand
 *
 * @param {string} dateString - Date string (YYYY-MM-DD)
 * @returns {Object} - { allHands, dealer, vulnerability }
 */
export const generateDailyHand = (dateString) => {
  const random = createSeededRandom(dateString);

  // Create a full deck
  const suits = ['S', 'H', 'D', 'C'];
  const ranks = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
  const deck = [];

  for (const suit of suits) {
    for (const rank of ranks) {
      deck.push({ rank, suit });
    }
  }

  // Shuffle deterministically
  shuffleArray(deck, random);

  // Deal to four hands
  const allHands = {
    north: deck.slice(0, 13),
    east: deck.slice(13, 26),
    south: deck.slice(26, 39),
    west: deck.slice(39, 52),
  };

  // Determine dealer based on date (rotates N E S W)
  const dealers = ['N', 'E', 'S', 'W'];
  const dayNumber = parseInt(dateString.replace(/-/g, ''), 10);
  const dealer = dealers[dayNumber % 4];

  // Determine vulnerability based on date (rotates None NS EW Both)
  const vulnerabilities = ['None', 'NS', 'EW', 'Both'];
  const vulnerability = vulnerabilities[dayNumber % 4];

  return { allHands, dealer, vulnerability };
};

/**
 * Calculate HCP for a hand
 * @param {Array<{rank: string, suit: string}>} hand
 * @returns {number}
 */
export const calculateHCP = (hand) => {
  const hcpValues = { A: 4, K: 3, Q: 2, J: 1 };
  return hand.reduce((sum, card) => sum + (hcpValues[card.rank] || 0), 0);
};

/**
 * Get stored daily hand data from localStorage
 * @returns {Object|null} - { date, result, streak, completedAt } or null
 */
export const getDailyStorage = () => {
  try {
    const stored = localStorage.getItem(DAILY_STORAGE_KEY);
    if (!stored) return null;
    return JSON.parse(stored);
  } catch (e) {
    console.error('Error reading daily storage:', e);
    return null;
  }
};

/**
 * Save daily hand result to localStorage
 * @param {Object} data - { date, result, streak, completedAt }
 */
export const saveDailyStorage = (data) => {
  try {
    localStorage.setItem(DAILY_STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    console.error('Error saving daily storage:', e);
  }
};

/**
 * Check if today's challenge is already completed
 * @returns {boolean}
 */
export const isTodayCompleted = () => {
  const stored = getDailyStorage();
  if (!stored) return false;
  return stored.date === getTodayString();
};

/**
 * Get current streak count
 * @returns {number}
 */
export const getCurrentStreak = () => {
  const stored = getDailyStorage();
  if (!stored) return 0;
  return stored.streak || 0;
};

/**
 * Calculate new streak after completing today
 * Streak continues if yesterday was also completed, otherwise resets to 1
 *
 * @param {string} todayString - Today's date string
 * @returns {number} - New streak count
 */
export const calculateNewStreak = (todayString) => {
  const stored = getDailyStorage();
  if (!stored) return 1;

  const lastDate = new Date(stored.date);
  const today = new Date(todayString);
  const diffDays = Math.floor((today - lastDate) / (1000 * 60 * 60 * 24));

  if (diffDays === 1) {
    // Yesterday was completed, continue streak
    return (stored.streak || 0) + 1;
  } else if (diffDays === 0) {
    // Already completed today (shouldn't happen but handle it)
    return stored.streak || 1;
  } else {
    // Streak broken, start fresh
    return 1;
  }
};

/**
 * Generate the 7-day streak calendar data
 * @returns {Array<{label: string, status: 'done'|'today'|'future', count?: number}>}
 */
export const generateStreakCalendar = () => {
  const today = new Date();
  const days = [];
  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const stored = getDailyStorage();

  // Get dates for the past 6 days + today
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateString = date.toISOString().split('T')[0];
    const dayLabel = dayLabels[date.getDay()];

    let status;
    if (i === 0) {
      // Today
      status = stored && stored.date === dateString ? 'done' : 'today';
    } else if (i > 0) {
      // Past days
      // For simplicity, we only track current streak, not full history
      // In a real app, you'd store all completion dates
      status = 'future'; // We'll treat unknown past days as not completed
    }

    days.push({
      label: dayLabel,
      status,
      count: status === 'done' ? 1 : undefined,
    });
  }

  return days;
};

/**
 * Check if a bid is valid given the current auction state
 *
 * @param {string} bid - The bid to check (e.g., "1H", "Pass", "X")
 * @param {Array<{bid: string, bidder: string}>} auction - Current auction
 * @returns {boolean}
 */
export const isBidLegal = (bid, auction) => {
  // Pass is always legal
  if (bid === 'Pass') return true;

  // Find the last non-pass bid
  const lastBid = [...auction].reverse().find(b => b.bid !== 'Pass');

  // Double (X) is legal only if opponent made the last bid
  if (bid === 'X') {
    if (!lastBid) return false;
    // Check if last bidder is an opponent (simplified: odd/even position)
    const lastBidIndex = auction.indexOf(lastBid);
    const currentIndex = auction.length;
    // Different parity means opponent
    return (lastBidIndex % 2) !== (currentIndex % 2);
  }

  // Redouble (XX) is legal only if opponent doubled
  if (bid === 'XX') {
    if (!lastBid) return false;
    return lastBid.bid === 'X';
  }

  // Regular bids must be higher than the last bid
  if (!lastBid || lastBid.bid === 'X' || lastBid.bid === 'XX') {
    // No previous bid or only double/redouble, any bid 1-level+ is legal
    return true;
  }

  // Compare bid levels
  const bidLevel = parseInt(bid[0], 10);
  const lastLevel = parseInt(lastBid.bid[0], 10);

  if (bidLevel > lastLevel) return true;
  if (bidLevel < lastLevel) return false;

  // Same level: compare strains
  const bidStrain = bid.slice(1);
  const lastStrain = lastBid.bid.slice(1);
  return STRAINS.indexOf(bidStrain) > STRAINS.indexOf(lastStrain);
};

/**
 * Get all legal bids for the current auction state
 *
 * @param {Array<{bid: string, bidder: string}>} auction - Current auction
 * @returns {Set<string>} - Set of legal bid strings
 */
export const getLegalBids = (auction) => {
  const legal = new Set();
  legal.add('Pass');

  // Check double/redouble
  if (isBidLegal('X', auction)) legal.add('X');
  if (isBidLegal('XX', auction)) legal.add('XX');

  // Check all level-strain combinations
  for (const level of BID_LEVELS) {
    for (const strain of STRAINS) {
      const bid = `${level}${strain}`;
      if (isBidLegal(bid, auction)) {
        legal.add(bid);
      }
    }
  }

  return legal;
};

/**
 * Check if the auction is complete (three consecutive passes after a bid)
 *
 * @param {Array<{bid: string, bidder: string}>} auction
 * @returns {boolean}
 */
export const isAuctionComplete = (auction) => {
  if (auction.length < 4) return false;

  // Check for three passes after a bid
  const lastThree = auction.slice(-3);
  if (!lastThree.every(b => b.bid === 'Pass')) return false;

  // Make sure there was a real bid before the three passes
  const priorBids = auction.slice(0, -3);
  return priorBids.some(b => b.bid !== 'Pass');
};

/**
 * Check if the auction resulted in all pass (no contract)
 *
 * @param {Array<{bid: string, bidder: string}>} auction
 * @returns {boolean}
 */
export const isAllPass = (auction) => {
  return auction.length >= 4 && auction.every(b => b.bid === 'Pass');
};

/**
 * Get the final contract from a completed auction
 *
 * @param {Array<{bid: string, bidder: string}>} auction
 * @returns {Object|null} - { level, strain, declarer, doubled, redoubled }
 */
export const getContractFromAuction = (auction) => {
  if (isAllPass(auction)) return null;

  // Find the last real bid (not Pass, X, XX)
  let lastBid = null;
  let lastBidIndex = -1;

  for (let i = auction.length - 1; i >= 0; i--) {
    const bid = auction[i].bid;
    if (bid !== 'Pass' && bid !== 'X' && bid !== 'XX') {
      lastBid = auction[i];
      lastBidIndex = i;
      break;
    }
  }

  if (!lastBid) return null;

  const level = parseInt(lastBid.bid[0], 10);
  const strain = lastBid.bid.slice(1);
  const declarer = lastBid.bidder;

  // Check for double/redouble after the last bid
  let doubled = false;
  let redoubled = false;

  for (let i = lastBidIndex + 1; i < auction.length; i++) {
    if (auction[i].bid === 'X') doubled = true;
    if (auction[i].bid === 'XX') redoubled = true;
  }

  return { level, strain, declarer, doubled, redoubled };
};

/**
 * Get the seats in bidding order starting from dealer
 *
 * @param {string} dealer - 'N', 'E', 'S', or 'W'
 * @returns {string[]} - Array of seats in order
 */
export const getBiddingOrder = (dealer) => {
  const order = ['N', 'E', 'S', 'W'];
  const startIndex = order.indexOf(dealer);
  return [...order.slice(startIndex), ...order.slice(0, startIndex)];
};

/**
 * Get whose turn it is to bid
 *
 * @param {Array<{bid: string, bidder: string}>} auction
 * @param {string} dealer
 * @returns {string} - 'N', 'E', 'S', or 'W'
 */
export const getCurrentBidder = (auction, dealer) => {
  const order = getBiddingOrder(dealer);
  return order[auction.length % 4];
};

// =============================================================================
// Mock Bidding Engine (TODO: Connect to real backend)
// =============================================================================

/**
 * TODO: Replace with actual API call to backend bidding engine
 * Mock AI bid generation for opponents
 *
 * @param {Object} hand - The AI player's hand
 * @param {Array<{bid: string, bidder: string}>} auction - Current auction
 * @param {string} bidder - Who is bidding
 * @returns {Object} - { bid, explanation }
 */
export const getAIBid = (hand, auction, bidder) => {
  // TODO: Call backend API: POST /api/get-next-bid
  // For now, simple mock logic

  const hcp = calculateHCP(hand);
  const legalBids = getLegalBids(auction);

  // If we can't open, pass
  if (auction.every(b => b.bid === 'Pass') && hcp < 12) {
    return { bid: 'Pass', explanation: 'Not enough strength to open' };
  }

  // Simple opening logic
  if (auction.every(b => b.bid === 'Pass')) {
    // Count suits
    const suitLengths = { S: 0, H: 0, D: 0, C: 0 };
    for (const card of hand) {
      suitLengths[card.suit]++;
    }

    // Find longest major
    if (suitLengths.S >= 5 && legalBids.has('1S')) {
      return { bid: '1S', explanation: '5+ spades, 12-21 HCP' };
    }
    if (suitLengths.H >= 5 && legalBids.has('1H')) {
      return { bid: '1H', explanation: '5+ hearts, 12-21 HCP' };
    }

    // Balanced? Open 1NT if 15-17
    const isBalanced =
      Math.max(...Object.values(suitLengths)) <= 4 &&
      Math.min(...Object.values(suitLengths)) >= 2;
    if (isBalanced && hcp >= 15 && hcp <= 17 && legalBids.has('1NT')) {
      return { bid: '1NT', explanation: 'Balanced, 15-17 HCP' };
    }

    // Open longest minor
    if (suitLengths.D >= suitLengths.C && legalBids.has('1D')) {
      return { bid: '1D', explanation: '3+ diamonds' };
    }
    if (legalBids.has('1C')) {
      return { bid: '1C', explanation: '3+ clubs' };
    }
  }

  // Default to pass for complex situations
  return { bid: 'Pass', explanation: 'Passing' };
};

// =============================================================================
// Mock Play Engine (TODO: Connect to real backend)
// =============================================================================

/**
 * TODO: Replace with actual API call to backend play engine
 * Mock AI card selection for play
 *
 * @param {Object} hand - The AI player's hand
 * @param {Array<{rank: string, suit: string}>} currentTrick - Cards played so far in trick
 * @param {string} trump - Trump suit or 'NT'
 * @param {string} position - 'N', 'E', 'S', or 'W'
 * @returns {Object} - { card, explanation }
 */
export const getAIPlay = (hand, currentTrick, trump, position) => {
  // TODO: Call backend API: POST /api/get-ai-play

  // Must follow suit if possible
  if (currentTrick.length > 0) {
    const leadSuit = currentTrick[0].suit;
    const cardsInSuit = hand.filter(c => c.suit === leadSuit);

    if (cardsInSuit.length > 0) {
      // Play lowest card in suit (simple logic)
      const card = cardsInSuit[cardsInSuit.length - 1];
      return { card, explanation: 'Following suit' };
    }

    // Can't follow - play a low card from any suit
    const card = hand[hand.length - 1];
    return { card, explanation: 'Discarding' };
  }

  // Leading - play first card (simplified)
  const card = hand[0];
  return { card, explanation: 'Leading' };
};

/**
 * TODO: Replace with actual DDS call
 * Mock DDS result for scoring
 *
 * @param {Object} allHands - All four hands
 * @param {Object} contract - The final contract
 * @returns {number} - Maximum tricks makeable by declarer
 */
export const getDDSResult = (allHands, contract) => {
  // TODO: Call backend API for DDS analysis
  // For now, return a mock value based on HCP
  if (!contract) return 0;

  const declarerHand =
    contract.declarer === 'N'
      ? allHands.north
      : contract.declarer === 'E'
      ? allHands.east
      : contract.declarer === 'S'
      ? allHands.south
      : allHands.west;

  const dummySeat =
    contract.declarer === 'N'
      ? 'S'
      : contract.declarer === 'E'
      ? 'W'
      : contract.declarer === 'S'
      ? 'N'
      : 'E';

  const dummyHand =
    dummySeat === 'N'
      ? allHands.north
      : dummySeat === 'E'
      ? allHands.east
      : dummySeat === 'S'
      ? allHands.south
      : allHands.west;

  const combinedHCP = calculateHCP(declarerHand) + calculateHCP(dummyHand);

  // Very rough estimate: 20 HCP -> 7 tricks, 30 HCP -> 10 tricks, 40 HCP -> 13 tricks
  const estimatedTricks = Math.min(13, Math.max(0, Math.round(6 + (combinedHCP - 20) * 0.35)));
  return estimatedTricks;
};

/**
 * Build a FlowResult object for emitting on completion
 *
 * @param {Object} params
 * @param {string} params.dateString - Today's date
 * @param {Array<{decisionId: string, category: string, playerAnswer: any, correctAnswer: any, isCorrect: boolean}>} params.decisions
 * @param {number} params.tricksVsOptimal - Difference from DDS optimal
 * @param {number} params.timeSpent - Milliseconds
 * @returns {Object} - FlowResult
 */
export const buildFlowResult = ({ dateString, decisions, tricksVsOptimal, timeSpent }) => {
  // Overall score: 100 if at optimal, minus 10 per trick below
  const overallScore = Math.max(0, 100 + tricksVsOptimal * 10);

  return {
    flowType: 'daily',
    handId: `daily-${dateString}`,
    timestamp: new Date().toISOString(),
    decisions,
    overallScore,
    timeSpent,
    conventionTags: [], // TODO: Extract from bidding decisions
  };
};

/**
 * Initial state for the Daily Hand flow
 *
 * @param {string} dateString
 * @returns {Object}
 */
export const getInitialState = (dateString) => {
  const { allHands, dealer, vulnerability } = generateDailyHand(dateString);
  const isCompleted = isTodayCompleted();
  const streak = getCurrentStreak();

  return {
    flowState: isCompleted ? FLOW_STATES.SUMMARY : FLOW_STATES.DEAL,
    dateString,
    allHands,
    dealer,
    vulnerability,
    auction: [],
    contract: null,
    currentTrick: [],
    tricksPlayed: 0,
    tricksTaken: { NS: 0, EW: 0 },
    ddsOptimal: null,
    decisions: [],
    startTime: Date.now(),
    isCompleted,
    streak,
    selectedLevel: null,
    selectedStrain: null,
  };
};

/**
 * Reducer for state transitions
 *
 * @param {Object} state
 * @param {Object} action - { type, payload }
 * @returns {Object} - New state
 */
export const dailyHandReducer = (state, action) => {
  switch (action.type) {
    case 'START_BIDDING':
      return {
        ...state,
        flowState: FLOW_STATES.BID,
      };

    case 'SELECT_LEVEL':
      return {
        ...state,
        selectedLevel: action.payload,
        selectedStrain: null, // Reset strain when level changes
      };

    case 'SELECT_STRAIN':
      return {
        ...state,
        selectedStrain: action.payload,
      };

    case 'MAKE_BID': {
      const { bid, bidder, explanation } = action.payload;
      const newAuction = [...state.auction, { bid, bidder, explanation }];

      // Check if auction is complete
      if (isAuctionComplete(newAuction) || isAllPass(newAuction)) {
        const contract = getContractFromAuction(newAuction);
        const ddsOptimal = contract ? getDDSResult(state.allHands, contract) : 0;

        if (!contract) {
          // All pass - go directly to summary
          return {
            ...state,
            auction: newAuction,
            contract: null,
            flowState: FLOW_STATES.SUMMARY,
            ddsOptimal: 0,
          };
        }

        return {
          ...state,
          auction: newAuction,
          contract,
          flowState: FLOW_STATES.PLAY,
          ddsOptimal,
        };
      }

      return {
        ...state,
        auction: newAuction,
        selectedLevel: null,
        selectedStrain: null,
      };
    }

    case 'PLAY_CARD': {
      const { card, player } = action.payload;
      const newTrick = [...state.currentTrick, { ...card, player }];

      if (newTrick.length === 4) {
        // Trick complete - determine winner
        // TODO: Implement proper trick evaluation
        const nsWon = Math.random() > 0.5; // Placeholder
        const newTricksTaken = {
          NS: state.tricksTaken.NS + (nsWon ? 1 : 0),
          EW: state.tricksTaken.EW + (nsWon ? 0 : 1),
        };
        const newTricksPlayed = state.tricksPlayed + 1;

        if (newTricksPlayed === 13) {
          // Hand complete
          return {
            ...state,
            currentTrick: [],
            tricksPlayed: newTricksPlayed,
            tricksTaken: newTricksTaken,
            flowState: FLOW_STATES.RESULT,
          };
        }

        return {
          ...state,
          currentTrick: [],
          tricksPlayed: newTricksPlayed,
          tricksTaken: newTricksTaken,
        };
      }

      return {
        ...state,
        currentTrick: newTrick,
      };
    }

    case 'SHOW_SUMMARY':
      return {
        ...state,
        flowState: FLOW_STATES.SUMMARY,
      };

    case 'COMPLETE_DAILY': {
      const { streak } = action.payload;
      return {
        ...state,
        isCompleted: true,
        streak,
      };
    }

    default:
      return state;
  }
};
