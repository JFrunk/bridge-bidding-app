/**
 * Card Component - Physics v2.0
 *
 * Fully scalable card using em units.
 * Safe-Zone: Rank and Suit centered within 1.6em strip.
 * Vertical Gap: 0.4em between Rank and Suit.
 * The Heavy Club: text-shadow + scale-110 for visual weight.
 */
import React from 'react';

const Card = ({ rank, suit, isHidden = false, customScaleClass = "text-base", onClick, selectable = false, selected = false }) => {
  const isRed = ['H', 'D', '♥', '♦'].includes(suit?.toUpperCase());
  const isClub = suit?.toUpperCase() === 'C' || suit === '♣';
  const isSpade = suit?.toUpperCase() === 'S' || suit === '♠';

  // Hidden card (back)
  if (isHidden) {
    return (
      <div className={`${customScaleClass} inline-block`}>
        <div className="w-[3.5em] h-[5.0em] bg-red-800 rounded-[0.35em] border-[0.06em] border-white shadow-[0.1em_0.1em_0.2em_rgba(0,0,0,0.3)]" />
      </div>
    );
  }

  const handleClick = (e) => {
    if (selectable && onClick) {
      onClick({ rank, suit });
    }
  };

  const handleTouchEnd = (e) => {
    if (selectable && onClick) {
      e.preventDefault();
      onClick({ rank, suit });
    }
  };

  // Build suit classes with Heavy Club rule
  const suitClasses = [
    'text-[1.3em] leading-none mt-[0.4em] text-center',
    isRed ? 'text-red-600' : 'text-gray-900',
    isClub ? 'drop-shadow-[0_0_0.05em_currentColor] scale-110' : '',
    isSpade ? 'scale-105' : ''
  ].filter(Boolean).join(' ');

  // Suit name for aria-label
  const suitName = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs',
                    'S': 'spades', 'H': 'hearts', 'D': 'diamonds', 'C': 'clubs'}[suit] || suit;

  return (
    <div
      className={`${customScaleClass} inline-block select-none ${selectable ? 'cursor-pointer transform transition-transform hover:-translate-y-[0.5em] hover:z-50' : ''} ${selected ? 'ring-2 ring-amber-500 -translate-y-[0.5em]' : ''}`}
      onClick={handleClick}
      onTouchEnd={handleTouchEnd}
      role={selectable ? 'button' : undefined}
      tabIndex={selectable ? 0 : undefined}
      aria-label={selectable ? `${rank} of ${suitName}` : undefined}
      onKeyDown={selectable ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleClick(e); } } : undefined}
    >
      <div className="w-[3.5em] h-[5.0em] bg-white rounded-[0.35em] border-[0.06em] border-gray-300 shadow-[0.1em_0.1em_0.2em_rgba(0,0,0,0.3)] flex flex-col items-start overflow-hidden">
        {/* Safe-Zone: 1.6em centered strip for rank + suit */}
        <div className="w-[1.6em] flex flex-col items-center pt-[0.3em]">
          <span className="text-[1.4em] font-black leading-none text-gray-900 text-center">
            {rank}
          </span>
          <span className={suitClasses}>
            {suit}
          </span>
        </div>
      </div>
    </div>
  );
};

export default Card;
