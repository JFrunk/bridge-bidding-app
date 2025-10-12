/**
 * Unit tests for cardUtils
 */

import {
  getSuitOrder,
  sortCards,
  groupCardsBySuit,
  rankToDisplay,
  getSuitColor,
  parseContract,
  formatContract
} from '../utils/cardUtils';

describe('getSuitOrder', () => {
  it('returns standard order for no trump', () => {
    expect(getSuitOrder(null)).toEqual(['♠', '♥', '♣', '♦']);
    expect(getSuitOrder('NT')).toEqual(['♠', '♥', '♣', '♦']);
  });

  it('returns correct order for trump suits', () => {
    expect(getSuitOrder('♠')).toEqual(['♠', '♥', '♣', '♦']);
    expect(getSuitOrder('♥')).toEqual(['♥', '♠', '♦', '♣']);
    expect(getSuitOrder('♦')).toEqual(['♦', '♠', '♥', '♣']);
    expect(getSuitOrder('♣')).toEqual(['♣', '♥', '♠', '♦']);
  });

  it('handles string strain formats', () => {
    expect(getSuitOrder('S')).toEqual(['♠', '♥', '♣', '♦']);
    expect(getSuitOrder('H')).toEqual(['♥', '♠', '♦', '♣']);
  });
});

describe('sortCards', () => {
  it('sorts cards by rank descending', () => {
    const cards = [
      { rank: '5', suit: '♠' },
      { rank: 'A', suit: '♠' },
      { rank: 'Q', suit: '♠' },
      { rank: 'K', suit: '♠' }
    ];

    const sorted = sortCards(cards);
    expect(sorted.map(c => c.rank)).toEqual(['A', 'K', 'Q', '5']);
  });

  it('handles Ten cards correctly', () => {
    const cards = [
      { rank: '9', suit: '♠' },
      { rank: 'T', suit: '♠' },
      { rank: 'J', suit: '♠' }
    ];

    const sorted = sortCards(cards);
    expect(sorted.map(c => c.rank)).toEqual(['J', 'T', '9']);
  });
});

describe('groupCardsBySuit', () => {
  it('groups cards by suit', () => {
    const cards = [
      { rank: 'A', suit: '♠' },
      { rank: 'K', suit: '♥' },
      { rank: 'Q', suit: '♠' },
      { rank: 'J', suit: '♦' }
    ];

    const grouped = groupCardsBySuit(cards);
    expect(grouped['♠']).toHaveLength(2);
    expect(grouped['♥']).toHaveLength(1);
    expect(grouped['♦']).toHaveLength(1);
    expect(grouped['♣']).toHaveLength(0);
  });
});

describe('rankToDisplay', () => {
  it('converts rank to display string', () => {
    expect(rankToDisplay('A')).toBe('A');
    expect(rankToDisplay('K')).toBe('K');
    expect(rankToDisplay('T')).toBe('10');
    expect(rankToDisplay('9')).toBe('9');
  });
});

describe('getSuitColor', () => {
  it('returns correct color classes', () => {
    expect(getSuitColor('♥')).toBe('suit-red');
    expect(getSuitColor('♦')).toBe('suit-red');
    expect(getSuitColor('♠')).toBe('suit-black');
    expect(getSuitColor('♣')).toBe('suit-black');
  });
});

describe('parseContract', () => {
  it('parses simple contracts', () => {
    expect(parseContract('3NT')).toEqual({
      level: 3,
      strain: 'NT',
      doubled: 0
    });

    expect(parseContract('4♠')).toEqual({
      level: 4,
      strain: '♠',
      doubled: 0
    });
  });

  it('parses doubled contracts', () => {
    expect(parseContract('6♥X')).toEqual({
      level: 6,
      strain: '♥',
      doubled: 1
    });

    expect(parseContract('7♣XX')).toEqual({
      level: 7,
      strain: '♣',
      doubled: 2
    });
  });

  it('returns null for invalid contracts', () => {
    expect(parseContract(null)).toBeNull();
    expect(parseContract('invalid')).toBeNull();
    expect(parseContract('8NT')).toBeNull();
  });
});

describe('formatContract', () => {
  it('formats contracts correctly', () => {
    expect(formatContract({
      level: 3,
      strain: 'NT',
      doubled: 0
    })).toBe('3NT');

    expect(formatContract({
      level: 4,
      strain: '♠',
      doubled: 1
    })).toBe('4♠X');

    expect(formatContract({
      level: 7,
      strain: '♥',
      doubled: 2
    })).toBe('7♥XX');
  });

  it('returns empty string for null contract', () => {
    expect(formatContract(null)).toBe('');
  });
});
