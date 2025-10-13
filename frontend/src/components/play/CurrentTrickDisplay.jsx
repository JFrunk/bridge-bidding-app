import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * CurrentTrickDisplay - Shows the current trick in progress
 * Follows "Rule of Three" and senior-friendly UX principles
 * PRIMARY visual element during card play
 */
export function CurrentTrickDisplay({ trick, trickWinner, trickComplete }) {
  console.log('🃏 CurrentTrickDisplay received:', { trick, trick_length: trick?.length, trickWinner, trickComplete });

  if (!trick || trick.length === 0) {
    return (
      <div className="flex items-center justify-center p-12 rounded-lg border-2 border-dashed border-gray-600 bg-bg-secondary">
        <p className="text-base text-gray-400">Waiting for cards...</p>
      </div>
    );
  }

  // DEFENSIVE: Only show the first 4 cards (a complete trick)
  const displayTrick = trick.slice(0, 4);
  if (trick.length > 4) {
    console.error('⚠️ WARNING: Trick has more than 4 cards!', {
      trick_length: trick.length,
      trick_data: trick
    });
  }

  const suitColor = (suit) => suit === '♥' || suit === '♦' ? 'text-suit-red' : 'text-suit-black';
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };

  // Position name mapping
  const positionNames = {
    'N': 'North',
    'E': 'East',
    'S': 'South',
    'W': 'West'
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Trick cards in a row */}
      <div className="flex flex-row gap-6 items-end">
        {displayTrick.map(({ card, position }, index) => {
          const displayRank = rankMap[card.rank] || card.rank;
          const isWinner = trickComplete && position === trickWinner;

          return (
            <div
              key={index}
              className={cn(
                "flex flex-col items-center gap-2 transition-all duration-300",
                isWinner && "transform scale-110"
              )}
            >
              {/* Position label */}
              <div className={cn(
                "text-sm font-bold px-3 py-1 rounded-md",
                isWinner ? "bg-highlight-winner text-bg-primary" : "bg-bg-tertiary text-gray-300"
              )}>
                {position}
              </div>

              {/* Card */}
              <div className={cn(
                "w-[70px] h-[100px] bg-white rounded-card border shadow-md flex flex-col items-center justify-center",
                "transition-all duration-300",
                isWinner && "ring-4 ring-highlight-winner shadow-xl"
              )}>
                <span className={cn("text-3xl font-bold", suitColor(card.suit))}>
                  {displayRank}
                </span>
                <span className={cn("text-2xl", suitColor(card.suit))}>
                  {card.suit}
                </span>
              </div>

              {/* Winner badge */}
              {isWinner && (
                <div className="text-xs font-bold text-highlight-winner animate-pulse">
                  Winner!
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Winner announcement */}
      {trickComplete && trickWinner && (
        <div className="text-lg font-bold text-highlight-winner bg-bg-secondary px-6 py-2 rounded-lg">
          {positionNames[trickWinner]} wins the trick!
        </div>
      )}
    </div>
  );
}
