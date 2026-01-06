/**
 * Seat utilities for bridge position calculations.
 *
 * This module provides a single source of truth for all seat-related
 * calculations across the frontend. Use these functions instead of
 * inline seat math to ensure consistency.
 *
 * Seat Mapping:
 *   NORTH = 0, EAST = 1, SOUTH = 2, WEST = 3
 *
 * The modulo-4 clock:
 *   - Partner is always +2 (opposite)
 *   - LHO (Left Hand Opponent) is always +1 (clockwise)
 *   - RHO (Right Hand Opponent) is always +3 (or -1)
 *
 * Usage:
 *   import { partner, lho, rho, relativePosition, displayName } from '../utils/seats';
 *
 *   // Get partner of South
 *   partner('S')  // Returns 'N'
 *
 *   // Get display name relative to user
 *   displayName('E', 'S')  // Returns 'LHO'
 *
 *   // Check if two seats are partners
 *   isPartner('N', 'S')  // Returns true
 */

// === CONSTANTS ===

// Integer indices (for modulo arithmetic)
export const NORTH = 0;
export const EAST = 1;
export const SOUTH = 2;
export const WEST = 3;

// Partnerships
export const NS = 0; // North-South
export const EW = 1; // East-West

// String representations
export const SEATS = ['N', 'E', 'S', 'W'];
export const SEAT_NAMES = { N: 'North', E: 'East', S: 'South', W: 'West' };
export const RELATIVE_NAMES = ['You', 'LHO', 'Partner', 'RHO'];

// Partnership sets
export const NS_SIDE = new Set(['N', 'S']);
export const EW_SIDE = new Set(['E', 'W']);

// Direct lookup maps (for performance when not using indices)
export const PARTNERS = { N: 'S', S: 'N', E: 'W', W: 'E' };
export const NEXT_PLAYER = { N: 'E', E: 'S', S: 'W', W: 'N' }; // LHO / clockwise
export const PREV_PLAYER = { N: 'W', E: 'N', S: 'E', W: 'S' }; // RHO / counter-clockwise


// === NORMALIZATION ===

/**
 * Normalize a position to single-letter format.
 *
 * @param {string|null|undefined} position - Position string ('North', 'N', 'north', etc.)
 * @returns {string} Single letter format ('N', 'E', 'S', 'W')
 *
 * @example
 * normalize('North') // 'N'
 * normalize('s') // 'S'
 * normalize(null) // 'N'
 */
export function normalize(position) {
  if (!position) return 'N'; // Default

  const pos = String(position).trim().toUpperCase();

  // Already single letter
  if (SEATS.includes(pos)) {
    return pos;
  }

  // Full name
  const fullMap = { NORTH: 'N', EAST: 'E', SOUTH: 'S', WEST: 'W' };
  return fullMap[pos] || 'N';
}


/**
 * Convert seat string to index (0-3).
 *
 * @param {string} seat - Seat string ('N', 'E', 'S', 'W' or full name)
 * @returns {number} Integer index (0=N, 1=E, 2=S, 3=W)
 */
export function seatIndex(seat) {
  return SEATS.indexOf(normalize(seat));
}


/**
 * Convert index to seat string.
 *
 * @param {number} index - Integer index (0-3, will be wrapped with modulo)
 * @returns {string} Seat string ('N', 'E', 'S', 'W')
 */
export function seatFromIndex(index) {
  // Handle negative indices correctly with ((index % 4) + 4) % 4
  return SEATS[((index % 4) + 4) % 4];
}


// === RELATIONSHIP FUNCTIONS ===

/**
 * Get the partner of a seat.
 *
 * @param {string} seat - Seat string
 * @returns {string} Partner's seat string
 *
 * @example
 * partner('S') // 'N'
 * partner('E') // 'W'
 */
export function partner(seat) {
  const s = normalize(seat);
  return PARTNERS[s];
}


/**
 * Get the Left Hand Opponent (next player clockwise).
 *
 * @param {string} seat - Seat string
 * @returns {string} LHO's seat string
 *
 * @example
 * lho('S') // 'W'
 * lho('N') // 'E'
 */
export function lho(seat) {
  const s = normalize(seat);
  return NEXT_PLAYER[s];
}


/**
 * Get the Right Hand Opponent (previous player clockwise).
 *
 * @param {string} seat - Seat string
 * @returns {string} RHO's seat string
 *
 * @example
 * rho('S') // 'E'
 * rho('N') // 'W'
 */
export function rho(seat) {
  const s = normalize(seat);
  return PREV_PLAYER[s];
}


/**
 * Get the partnership of a seat.
 *
 * @param {string} seat - Seat string
 * @returns {number} Partnership index (0=NS, 1=EW)
 */
export function partnership(seat) {
  return seatIndex(seat) % 2;
}


/**
 * Get the partnership name of a seat.
 *
 * @param {string} seat - Seat string
 * @returns {string} Partnership string ('NS' or 'EW')
 */
export function partnershipStr(seat) {
  return partnership(seat) === NS ? 'NS' : 'EW';
}


/**
 * Check if two seats are partners.
 *
 * @param {string} seat1 - First seat string
 * @param {string} seat2 - Second seat string
 * @returns {boolean} True if seats are partners
 */
export function isPartner(seat1, seat2) {
  return partner(seat1) === normalize(seat2);
}


/**
 * Check if two seats are opponents.
 *
 * @param {string} seat1 - First seat string
 * @param {string} seat2 - Second seat string
 * @returns {boolean} True if seats are opponents
 */
export function isOpponent(seat1, seat2) {
  return partnership(seat1) !== partnership(seat2);
}


/**
 * Check if two seats are on the same side (partners).
 *
 * @param {string} seat1 - First seat string
 * @param {string} seat2 - Second seat string
 * @returns {boolean} True if seats are on the same partnership
 */
export function sameSide(seat1, seat2) {
  return partnership(seat1) === partnership(seat2);
}


// === RELATIVE POSITION ===

/**
 * Get the relative position of target from hero's perspective.
 *
 * Uses modulo-4 clock arithmetic:
 *   0 = Self
 *   1 = LHO (Left Hand Opponent)
 *   2 = Partner
 *   3 = RHO (Right Hand Opponent)
 *
 * @param {string} target - Target seat string
 * @param {string} hero - Hero/user seat string
 * @returns {number} Relative position index (0-3)
 *
 * @example
 * relativePosition('W', 'S') // 1 (LHO)
 * relativePosition('N', 'S') // 2 (Partner)
 * relativePosition('E', 'S') // 3 (RHO)
 */
export function relativePosition(target, hero) {
  const diff = seatIndex(target) - seatIndex(hero);
  return ((diff % 4) + 4) % 4; // Handle negative correctly
}


/**
 * Get a display name for a seat.
 *
 * @param {string} seat - Target seat string
 * @param {string} [hero='S'] - Hero/user seat string
 * @param {boolean} [relative=true] - If true, return relative name ('Partner');
 *                                    if false, return absolute name ('North')
 * @returns {string} Display name string
 *
 * @example
 * displayName('N', 'S') // 'Partner'
 * displayName('N', 'S', false) // 'North'
 * displayName('E', 'S') // 'RHO'
 */
export function displayName(seat, hero = 'S', relative = true) {
  const s = normalize(seat);
  if (relative) {
    const rel = relativePosition(s, hero);
    return RELATIVE_NAMES[rel];
  }
  return SEAT_NAMES[s];
}


/**
 * Get the role description for a bidder relative to the user.
 *
 * @param {string} bidder - Bidder's seat string
 * @param {string} user - User's seat string
 * @returns {string} Role string with seat name, e.g., 'North (Partner)'
 *
 * @example
 * bidderRole('N', 'S') // 'North (Partner)'
 * bidderRole('E', 'S') // 'East (Opponent)'
 * bidderRole('S', 'S') // 'South (You)'
 */
export function bidderRole(bidder, user) {
  const b = normalize(bidder);
  const u = normalize(user);

  const rel = relativePosition(b, u);
  const seatName = SEAT_NAMES[b];

  if (rel === 0) {
    return `${seatName} (You)`;
  } else if (rel === 2) {
    return `${seatName} (Partner)`;
  } else {
    return `${seatName} (Opponent)`;
  }
}


// === PLAY PHASE HELPERS ===

/**
 * Get the dummy seat given the declarer.
 *
 * @param {string} declarer - Declarer's seat string
 * @returns {string} Dummy's seat string (declarer's partner)
 */
export function dummy(declarer) {
  return partner(declarer);
}


/**
 * Get the opening leader seat given the declarer.
 *
 * @param {string} declarer - Declarer's seat string
 * @returns {string} Opening leader's seat string (LHO of declarer)
 */
export function openingLeader(declarer) {
  return lho(declarer);
}


/**
 * Check if a seat is on the declaring side.
 *
 * @param {string} seat - Seat to check
 * @param {string} declarer - Declarer's seat string
 * @returns {boolean} True if seat is declarer or dummy
 */
export function isDeclaringSide(seat, declarer) {
  return sameSide(seat, declarer);
}


/**
 * Check if a seat is on the defending side.
 *
 * @param {string} seat - Seat to check
 * @param {string} declarer - Declarer's seat string
 * @returns {boolean} True if seat is a defender
 */
export function isDefendingSide(seat, declarer) {
  return !isDeclaringSide(seat, declarer);
}


// === BIDDING PHASE HELPERS ===

/**
 * Get the active seat during bidding.
 *
 * @param {string} dealer - Dealer's seat string
 * @param {number} bidCount - Number of bids made so far
 * @returns {string} Active seat string
 */
export function activeSeatBidding(dealer, bidCount) {
  const dealerIdx = seatIndex(dealer);
  return seatFromIndex(dealerIdx + bidCount);
}


/**
 * Get the active seat during play.
 *
 * @param {string} trickLeader - Trick leader's seat string
 * @param {number} cardsPlayed - Number of cards played in current trick (0-3)
 * @returns {string} Active seat string
 */
export function activeSeatPlay(trickLeader, cardsPlayed) {
  const leaderIdx = seatIndex(trickLeader);
  return seatFromIndex(leaderIdx + cardsPlayed);
}


/**
 * Determine success from NS perspective.
 *
 * @param {boolean} nsIsDeclarer - Whether NS is the declaring side
 * @param {number} actualTricksNs - Actual tricks NS took
 * @param {number} requiredTricks - Tricks required to make/set contract
 * @returns {boolean} True if NS succeeded (made contract or set opponents)
 */
export function nsSuccess(nsIsDeclarer, actualTricksNs, requiredTricks) {
  if (nsIsDeclarer) {
    // NS declaring: need to make the contract
    return actualTricksNs >= requiredTricks;
  } else {
    // NS defending: need to take enough tricks to set the contract
    // If EW needs 'requiredTricks', NS needs (14 - requiredTricks) to set
    // Equivalently: NS succeeds if EW got fewer than requiredTricks
    // Since EW tricks = 13 - actualTricksNs, EW < required means:
    // 13 - actualTricksNs < requiredTricks
    // actualTricksNs > 13 - requiredTricks
    return actualTricksNs > (13 - requiredTricks);
  }
}
