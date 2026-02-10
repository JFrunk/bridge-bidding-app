/**
 * SuitRow Component - Physics v2.0
 *
 * Displays a row of cards for a single suit with dynamic overlap spacing.
 * Spacing adjusts based on card count to prevent overflow.
 *
 * Uses em-based dimensions for scalability with customScaleClass.
 */
import React from 'react';
import Card from './Card';

const SuitRow = ({ suit, cards, customScaleClass = "text-base" }) => {
  if (!cards || cards.length === 0) return null;

  const count = cards.length;

  // Dynamic spacing based on card count
  let spacingClass = '-space-x-[1.2em]';
  if (count === 5) spacingClass = '-space-x-[1.4em]';
  if (count === 6) spacingClass = '-space-x-[1.6em]';
  if (count >= 7) spacingClass = '-space-x-[1.9em]';

  // Suit color for the indicator
  const isRed = ['H', 'D', '♥', '♦'].includes(suit.toUpperCase());
  const suitColor = isRed ? 'text-red-600' : 'text-gray-900';

  return (
    <div className="flex flex-row items-center gap-[0.5em] min-h-[4em] max-w-[18em]">
      {/* Suit indicator */}
      <div className={`w-[1.2em] flex-shrink-0 font-bold text-[1.2em] ${suitColor} text-center`}>
        {suit}
      </div>
      {/* Cards with dynamic overlap */}
      <div className={`flex flex-row ${spacingClass}`}>
        {cards.map((card, idx) => (
          <div key={idx} style={{ zIndex: 10 + idx }}>
            <Card
              rank={card.rank}
              suit={card.suit}
              customScaleClass={customScaleClass}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default SuitRow;
