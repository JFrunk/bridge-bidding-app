import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * LastTrickOverlay - Shows the last completed trick in compass layout
 *
 * Displays when user clicks "Last Trick" button, auto-dismisses after 3 seconds.
 * Uses same card layout as CurrentTrickDisplay for visual consistency.
 */
export function LastTrickOverlay({ trick, trickNumber, onClose }) {
  if (!trick || !trick.cards) return null;

  const suitColor = (suit) => suit === '♥' || suit === '♦' ? 'text-suit-red' : 'text-suit-black';
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };

  // Create a map of position -> card from trick data
  const cardsByPosition = {};
  trick.cards.forEach(({ card, position }) => {
    cardsByPosition[position] = card;
  });

  // Card component for trick display (same as CurrentTrickDisplay)
  const TrickCard = ({ card, position, isWinner }) => {
    if (!card) return null;

    const displayRank = rankMap[card.rank] || card.rank;

    return (
      <div
        className={cn(
          "w-[70px] h-[100px] bg-white rounded-card shadow-md flex flex-col items-center justify-center",
          "transition-all duration-300",
          // Bold border (ring) for winner
          isWinner ? "ring-4 ring-yellow-400 shadow-2xl border-0" : "border border-gray-400",
          // Slight scale up for winner
          isWinner && "scale-105"
        )}
      >
        <span className={cn("text-3xl font-bold", suitColor(card.suit))}>
          {displayRank}
        </span>
        <span className={cn("text-2xl", suitColor(card.suit))}>
          {card.suit}
        </span>
      </div>
    );
  };

  // Position names for display
  const positionNames = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };

  return (
    <div
      className="relative flex flex-col items-center justify-center w-full h-full min-h-[350px] cursor-pointer"
      onClick={onClose}
      title="Click to dismiss"
    >
      {/* Header showing trick number and winner */}
      <div className="absolute top-0 left-0 right-0 text-center py-2 bg-bg-secondary/80 rounded-t-lg">
        <p className="text-sm text-gray-300">
          <span className="font-semibold">Trick #{trickNumber}</span>
          {' '}&mdash;{' '}
          Won by <span className="font-semibold text-yellow-400">{positionNames[trick.winner]}</span>
        </p>
      </div>

      {/* Compass layout: North (top), East (right), South (bottom), West (left) */}
      <div className="relative w-full h-full flex items-center justify-center mt-8">
        {/* North card - Top center */}
        {cardsByPosition.N && (
          <div className="absolute top-0 left-1/2 -translate-x-1/2">
            <TrickCard
              card={cardsByPosition.N}
              position="N"
              isWinner={trick.winner === 'N'}
            />
          </div>
        )}

        {/* East card - Right center */}
        {cardsByPosition.E && (
          <div className="absolute right-0 top-1/2 -translate-y-1/2">
            <TrickCard
              card={cardsByPosition.E}
              position="E"
              isWinner={trick.winner === 'E'}
            />
          </div>
        )}

        {/* South card - Bottom center */}
        {cardsByPosition.S && (
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2">
            <TrickCard
              card={cardsByPosition.S}
              position="S"
              isWinner={trick.winner === 'S'}
            />
          </div>
        )}

        {/* West card - Left center */}
        {cardsByPosition.W && (
          <div className="absolute left-0 top-1/2 -translate-y-1/2">
            <TrickCard
              card={cardsByPosition.W}
              position="W"
              isWinner={trick.winner === 'W'}
            />
          </div>
        )}

        {/* Center indicator */}
        <div className="text-gray-500 text-xs opacity-60">
          (click to dismiss)
        </div>
      </div>
    </div>
  );
}
