/**
 * BidChip Component - Physics v2.0
 *
 * Fully scalable bid chip using em units.
 * Suit Colors: Hearts/Diamonds = suit-red; Spades/Clubs/NT = suit-black.
 */
import React from 'react';
import { getSuitColorClass } from '../../utils/suitColors';

const BidChip = ({ bid }) => {
  if (!bid) return null;

  const bidStr = String(bid).toUpperCase();
  const isSpecial = ['PASS', 'DBL', 'RDBL', 'X', 'XX'].includes(bidStr);

  // Extract rank (numbers) and suit (symbols/letters)
  const rank = bidStr.match(/^\d+/) ? bidStr.match(/^\d+/)[0] : '';
  const suit = bidStr.replace(/^\d+/, '').trim();

  // Suit color helper (delegating to shared utility)
  const getSuitColor = (s) => getSuitColorClass(s);

  return (
    <div className="inline-flex items-center justify-center bg-white rounded-[0.3em] px-[0.5em] py-[0.1em] shadow-[0.1em_0.1em_0.1em_rgba(0,0,0,0.1)] border border-gray-200 min-w-[3.2em] h-[2em] mx-auto">
      {isSpecial ? (
        <span className="text-[0.8em] font-bold text-suit-black uppercase">
          {bidStr}
        </span>
      ) : (
        <div className="flex items-center gap-[0.1em] font-bold text-[1em] leading-none">
          <span className="text-suit-black">{rank}</span>
          <span className={getSuitColor(suit)}>{suit}</span>
        </div>
      )}
    </div>
  );
};

// Named export for existing imports
export { BidChip };
export default BidChip;
