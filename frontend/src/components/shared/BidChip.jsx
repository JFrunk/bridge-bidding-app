/**
 * BidChip Component - Physics v2.0
 *
 * Fully scalable bid chip using em units.
 * Suit Colors: Hearts/Diamonds = Red-600; Spades/Clubs/NT = Gray-900.
 */
import React from 'react';

const BidChip = ({ bid }) => {
  if (!bid) return null;

  const bidStr = String(bid).toUpperCase();
  const isSpecial = ['PASS', 'DBL', 'RDBL', 'X', 'XX'].includes(bidStr);

  // Extract rank (numbers) and suit (symbols/letters)
  const rank = bidStr.match(/^\d+/) ? bidStr.match(/^\d+/)[0] : '';
  const suit = bidStr.replace(/^\d+/, '').trim();

  // Suit color helper
  const getSuitColor = (s) => {
    if (['H', 'D', '♥', '♦'].includes(s)) return 'text-red-600';
    return 'text-gray-900';
  };

  return (
    <div className="inline-flex items-center justify-center bg-white rounded-[0.3em] px-[0.5em] py-[0.1em] shadow-[0.1em_0.1em_0.1em_rgba(0,0,0,0.1)] border border-gray-200 min-w-[3.2em] h-[2em] mx-auto">
      {isSpecial ? (
        <span className="text-[0.8em] font-bold text-gray-900 uppercase">
          {bidStr}
        </span>
      ) : (
        <div className="flex items-center gap-[0.1em] font-bold text-[1em] leading-none">
          <span className="text-gray-900">{rank}</span>
          <span className={getSuitColor(suit)}>{suit}</span>
        </div>
      )}
    </div>
  );
};

// Named export for existing imports
export { BidChip };
export default BidChip;
