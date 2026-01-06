/**
 * Unit tests for seats utility module.
 *
 * Tests the modulo-4 clock arithmetic and all helper functions
 * to ensure consistent seat calculations across the application.
 */

import {
  // Constants
  NORTH, EAST, SOUTH, WEST, NS, EW,
  SEATS, SEAT_NAMES, PARTNERS, NS_SIDE, EW_SIDE,
  // Functions
  normalize, seatIndex, seatFromIndex,
  partner, lho, rho,
  partnership, partnershipStr, isPartner, isOpponent, sameSide,
  relativePosition, displayName, bidderRole,
  dummy, openingLeader, isDeclaringSide, isDefendingSide,
  activeSeatBidding, activeSeatPlay, nsSuccess
} from './seats';


describe('Constants', () => {
  test('seat indices are correct', () => {
    expect(NORTH).toBe(0);
    expect(EAST).toBe(1);
    expect(SOUTH).toBe(2);
    expect(WEST).toBe(3);
  });

  test('partnership indices are correct', () => {
    expect(NS).toBe(0);
    expect(EW).toBe(1);
  });

  test('SEATS list is correct', () => {
    expect(SEATS).toEqual(['N', 'E', 'S', 'W']);
  });

  test('PARTNERS map is correct', () => {
    expect(PARTNERS).toEqual({ N: 'S', S: 'N', E: 'W', W: 'E' });
  });

  test('NS_SIDE contains N and S', () => {
    expect(NS_SIDE.has('N')).toBe(true);
    expect(NS_SIDE.has('S')).toBe(true);
    expect(NS_SIDE.has('E')).toBe(false);
  });

  test('EW_SIDE contains E and W', () => {
    expect(EW_SIDE.has('E')).toBe(true);
    expect(EW_SIDE.has('W')).toBe(true);
    expect(EW_SIDE.has('N')).toBe(false);
  });
});


describe('normalize', () => {
  test('normalizes single letters', () => {
    expect(normalize('N')).toBe('N');
    expect(normalize('E')).toBe('E');
    expect(normalize('S')).toBe('S');
    expect(normalize('W')).toBe('W');
  });

  test('normalizes lowercase', () => {
    expect(normalize('n')).toBe('N');
    expect(normalize('e')).toBe('E');
    expect(normalize('s')).toBe('S');
    expect(normalize('w')).toBe('W');
  });

  test('normalizes full names', () => {
    expect(normalize('North')).toBe('N');
    expect(normalize('East')).toBe('E');
    expect(normalize('South')).toBe('S');
    expect(normalize('West')).toBe('W');
  });

  test('normalizes uppercase full names', () => {
    expect(normalize('NORTH')).toBe('N');
    expect(normalize('SOUTH')).toBe('S');
  });

  test('defaults to N for null/empty', () => {
    expect(normalize(null)).toBe('N');
    expect(normalize(undefined)).toBe('N');
    expect(normalize('')).toBe('N');
  });

  test('handles whitespace', () => {
    expect(normalize('  N  ')).toBe('N');
    expect(normalize(' South ')).toBe('S');
  });
});


describe('seatIndex and seatFromIndex', () => {
  test('converts seat to index', () => {
    expect(seatIndex('N')).toBe(0);
    expect(seatIndex('E')).toBe(1);
    expect(seatIndex('S')).toBe(2);
    expect(seatIndex('W')).toBe(3);
  });

  test('converts full name to index', () => {
    expect(seatIndex('North')).toBe(0);
    expect(seatIndex('South')).toBe(2);
  });

  test('converts index to seat', () => {
    expect(seatFromIndex(0)).toBe('N');
    expect(seatFromIndex(1)).toBe('E');
    expect(seatFromIndex(2)).toBe('S');
    expect(seatFromIndex(3)).toBe('W');
  });

  test('wraps positive indices', () => {
    expect(seatFromIndex(4)).toBe('N');
    expect(seatFromIndex(5)).toBe('E');
    expect(seatFromIndex(6)).toBe('S');
    expect(seatFromIndex(7)).toBe('W');
    expect(seatFromIndex(8)).toBe('N');
  });

  test('wraps negative indices', () => {
    expect(seatFromIndex(-1)).toBe('W');
    expect(seatFromIndex(-2)).toBe('S');
    expect(seatFromIndex(-3)).toBe('E');
    expect(seatFromIndex(-4)).toBe('N');
  });
});


describe('partner', () => {
  test('returns correct partner', () => {
    expect(partner('N')).toBe('S');
    expect(partner('S')).toBe('N');
    expect(partner('E')).toBe('W');
    expect(partner('W')).toBe('E');
  });

  test('partner of partner is self', () => {
    SEATS.forEach(seat => {
      expect(partner(partner(seat))).toBe(seat);
    });
  });

  test('works with full names', () => {
    expect(partner('North')).toBe('S');
    expect(partner('South')).toBe('N');
  });
});


describe('lho and rho', () => {
  test('lho returns next player clockwise', () => {
    expect(lho('N')).toBe('E');
    expect(lho('E')).toBe('S');
    expect(lho('S')).toBe('W');
    expect(lho('W')).toBe('N');
  });

  test('rho returns previous player clockwise', () => {
    expect(rho('N')).toBe('W');
    expect(rho('E')).toBe('N');
    expect(rho('S')).toBe('E');
    expect(rho('W')).toBe('S');
  });

  test('lho and rho are inverses', () => {
    SEATS.forEach(seat => {
      expect(lho(rho(seat))).toBe(seat);
      expect(rho(lho(seat))).toBe(seat);
    });
  });
});


describe('partnership functions', () => {
  test('partnership returns correct index', () => {
    expect(partnership('N')).toBe(NS);
    expect(partnership('S')).toBe(NS);
    expect(partnership('E')).toBe(EW);
    expect(partnership('W')).toBe(EW);
  });

  test('partnershipStr returns correct string', () => {
    expect(partnershipStr('N')).toBe('NS');
    expect(partnershipStr('S')).toBe('NS');
    expect(partnershipStr('E')).toBe('EW');
    expect(partnershipStr('W')).toBe('EW');
  });

  test('isPartner identifies partners', () => {
    expect(isPartner('N', 'S')).toBe(true);
    expect(isPartner('S', 'N')).toBe(true);
    expect(isPartner('E', 'W')).toBe(true);
    expect(isPartner('W', 'E')).toBe(true);
    expect(isPartner('N', 'E')).toBe(false);
    expect(isPartner('N', 'W')).toBe(false);
  });

  test('isOpponent identifies opponents', () => {
    expect(isOpponent('N', 'E')).toBe(true);
    expect(isOpponent('N', 'W')).toBe(true);
    expect(isOpponent('S', 'E')).toBe(true);
    expect(isOpponent('N', 'S')).toBe(false);
  });

  test('sameSide identifies same partnership', () => {
    expect(sameSide('N', 'S')).toBe(true);
    expect(sameSide('E', 'W')).toBe(true);
    expect(sameSide('N', 'E')).toBe(false);
  });
});


describe('relativePosition', () => {
  test('self is position 0', () => {
    SEATS.forEach(seat => {
      expect(relativePosition(seat, seat)).toBe(0);
    });
  });

  test('partner is position 2', () => {
    SEATS.forEach(seat => {
      expect(relativePosition(partner(seat), seat)).toBe(2);
    });
  });

  test('lho is position 1', () => {
    SEATS.forEach(seat => {
      expect(relativePosition(lho(seat), seat)).toBe(1);
    });
  });

  test('rho is position 3', () => {
    SEATS.forEach(seat => {
      expect(relativePosition(rho(seat), seat)).toBe(3);
    });
  });

  test('from south perspective', () => {
    expect(relativePosition('S', 'S')).toBe(0); // Self
    expect(relativePosition('W', 'S')).toBe(1); // LHO
    expect(relativePosition('N', 'S')).toBe(2); // Partner
    expect(relativePosition('E', 'S')).toBe(3); // RHO
  });

  test('from north perspective', () => {
    expect(relativePosition('N', 'N')).toBe(0); // Self
    expect(relativePosition('E', 'N')).toBe(1); // LHO
    expect(relativePosition('S', 'N')).toBe(2); // Partner
    expect(relativePosition('W', 'N')).toBe(3); // RHO
  });
});


describe('displayName', () => {
  test('relative names from south', () => {
    expect(displayName('S', 'S')).toBe('You');
    expect(displayName('W', 'S')).toBe('LHO');
    expect(displayName('N', 'S')).toBe('Partner');
    expect(displayName('E', 'S')).toBe('RHO');
  });

  test('relative names from north', () => {
    expect(displayName('N', 'N')).toBe('You');
    expect(displayName('E', 'N')).toBe('LHO');
    expect(displayName('S', 'N')).toBe('Partner');
    expect(displayName('W', 'N')).toBe('RHO');
  });

  test('absolute names', () => {
    expect(displayName('N', 'S', false)).toBe('North');
    expect(displayName('E', 'S', false)).toBe('East');
    expect(displayName('S', 'S', false)).toBe('South');
    expect(displayName('W', 'S', false)).toBe('West');
  });
});


describe('bidderRole', () => {
  test('from south perspective', () => {
    expect(bidderRole('S', 'S')).toBe('South (You)');
    expect(bidderRole('N', 'S')).toBe('North (Partner)');
    expect(bidderRole('E', 'S')).toBe('East (Opponent)');
    expect(bidderRole('W', 'S')).toBe('West (Opponent)');
  });

  test('from east perspective', () => {
    expect(bidderRole('E', 'E')).toBe('East (You)');
    expect(bidderRole('W', 'E')).toBe('West (Partner)');
    expect(bidderRole('N', 'E')).toBe('North (Opponent)');
    expect(bidderRole('S', 'E')).toBe('South (Opponent)');
  });
});


describe('play phase helpers', () => {
  test('dummy is partner of declarer', () => {
    expect(dummy('S')).toBe('N');
    expect(dummy('N')).toBe('S');
    expect(dummy('E')).toBe('W');
    expect(dummy('W')).toBe('E');
  });

  test('opening leader is LHO of declarer', () => {
    expect(openingLeader('S')).toBe('W');
    expect(openingLeader('N')).toBe('E');
    expect(openingLeader('E')).toBe('S');
    expect(openingLeader('W')).toBe('N');
  });

  test('isDeclaringSide identifies declarer and dummy', () => {
    // South declares
    expect(isDeclaringSide('S', 'S')).toBe(true);  // Declarer
    expect(isDeclaringSide('N', 'S')).toBe(true);  // Dummy
    expect(isDeclaringSide('E', 'S')).toBe(false); // Defender
    expect(isDeclaringSide('W', 'S')).toBe(false); // Defender
  });

  test('isDefendingSide identifies defenders', () => {
    // South declares
    expect(isDefendingSide('E', 'S')).toBe(true);
    expect(isDefendingSide('W', 'S')).toBe(true);
    expect(isDefendingSide('S', 'S')).toBe(false);
    expect(isDefendingSide('N', 'S')).toBe(false);
  });
});


describe('bidding phase helpers', () => {
  test('activeSeatBidding from north dealer', () => {
    expect(activeSeatBidding('N', 0)).toBe('N');
    expect(activeSeatBidding('N', 1)).toBe('E');
    expect(activeSeatBidding('N', 2)).toBe('S');
    expect(activeSeatBidding('N', 3)).toBe('W');
    expect(activeSeatBidding('N', 4)).toBe('N');
  });

  test('activeSeatBidding from east dealer', () => {
    expect(activeSeatBidding('E', 0)).toBe('E');
    expect(activeSeatBidding('E', 1)).toBe('S');
    expect(activeSeatBidding('E', 2)).toBe('W');
    expect(activeSeatBidding('E', 3)).toBe('N');
  });

  test('activeSeatPlay', () => {
    // West leads
    expect(activeSeatPlay('W', 0)).toBe('W');
    expect(activeSeatPlay('W', 1)).toBe('N');
    expect(activeSeatPlay('W', 2)).toBe('E');
    expect(activeSeatPlay('W', 3)).toBe('S');
  });
});


describe('nsSuccess', () => {
  test('NS declaring - made contract', () => {
    // NS needs 10 tricks (4H), they got 10
    expect(nsSuccess(true, 10, 10)).toBe(true);
    // NS needs 10 tricks, they got 11
    expect(nsSuccess(true, 11, 10)).toBe(true);
  });

  test('NS declaring - failed contract', () => {
    // NS needs 10 tricks, they got 9
    expect(nsSuccess(true, 9, 10)).toBe(false);
  });

  test('NS defending - set contract', () => {
    // EW needs 10 tricks to make 4H
    // NS needs to take 4+ tricks to set (13 - 10 + 1 = 4)
    // If NS took 4 tricks, EW got 9 < 10, so NS succeeded
    expect(nsSuccess(false, 4, 10)).toBe(true);
    // If NS took 5 tricks, EW got 8 < 10, so NS succeeded
    expect(nsSuccess(false, 5, 10)).toBe(true);
  });

  test('NS defending - failed to set', () => {
    // EW needs 10 tricks
    // If NS took 3 tricks, EW got 10 >= 10, so NS failed
    expect(nsSuccess(false, 3, 10)).toBe(false);
    // If NS took 2 tricks, EW got 11, so NS failed
    expect(nsSuccess(false, 2, 10)).toBe(false);
  });

  test('3NT edge cases', () => {
    // 3NT requires 9 tricks
    // NS declaring with 9 tricks - success
    expect(nsSuccess(true, 9, 9)).toBe(true);
    // NS defending, took 5 tricks (EW got 8) - success (set)
    expect(nsSuccess(false, 5, 9)).toBe(true);
    // NS defending, took 4 tricks (EW got 9) - failure (made)
    expect(nsSuccess(false, 4, 9)).toBe(false);
  });
});


describe('modulo-4 properties', () => {
  test('full rotation returns to start', () => {
    let seat = 'S';
    for (let i = 0; i < 4; i++) {
      seat = lho(seat);
    }
    expect(seat).toBe('S');
  });

  test('all positions reachable via LHO', () => {
    SEATS.forEach(start => {
      const visited = new Set();
      let current = start;
      for (let i = 0; i < 4; i++) {
        visited.add(current);
        current = lho(current);
      }
      expect(visited.size).toBe(4);
    });
  });

  test('sum of relative positions is 6', () => {
    SEATS.forEach(hero => {
      const total = SEATS.reduce((sum, target) => sum + relativePosition(target, hero), 0);
      expect(total).toBe(6); // 0 + 1 + 2 + 3
    });
  });
});
