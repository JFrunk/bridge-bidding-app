import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * LastTrickOverlay - Shows the last completed trick in compass layout
 *
 * Displays when user clicks "Last Trick" button, auto-dismisses after 3 seconds.
 * Uses same card layout as CurrentTrickDisplay for visual consistency.
 *
 * CRITICAL: Uses inline styles for colors to ensure visibility regardless of Tailwind config
 */
export function LastTrickOverlay({ trick, trickNumber, onClose }) {
  if (!trick || !trick.cards) return null;

  // Use inline styles for guaranteed color visibility (not Tailwind classes)
  const getSuitStyle = (suit) => ({
    color: suit === '♥' || suit === '♦' ? '#c41e3a' : '#000000'  // Red or black
  });
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };

  // Create a map of position -> card from trick data
  const cardsByPosition = {};
  trick.cards.forEach(({ card, position }) => {
    cardsByPosition[position] = card;
  });

  // Card component for trick display - sized to match CurrentTrickDisplay (48x66px)
  // CRITICAL: Uses inline styles for text color to ensure visibility (black text on white card)
  const TrickCard = ({ card, position, isWinner }) => {
    if (!card) return null;

    const displayRank = rankMap[card.rank] || card.rank;
    const suitStyle = getSuitStyle(card.suit);

    return (
      <div
        className={cn(
          "w-[48px] h-[66px] bg-white rounded shadow-md flex flex-col items-center justify-center",
          "transition-all duration-300",
          // Bold border (ring) for winner
          isWinner ? "ring-2 ring-yellow-400 shadow-xl border-0" : "border border-gray-300",
          // Slight scale up for winner
          isWinner && "scale-105"
        )}
      >
        <span className="text-lg font-bold leading-none" style={suitStyle}>
          {displayRank}
        </span>
        <span className="text-sm leading-none" style={suitStyle}>
          {card.suit}
        </span>
      </div>
    );
  };

  // Position names for display
  const positionNames = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };

  return (
    <div
      className="relative flex flex-col items-center justify-center w-[200px] h-[180px] cursor-pointer mx-auto"
      onClick={onClose}
      title="Click to dismiss"
    >
      {/* Header showing trick number and winner */}
      <div className="absolute -top-6 left-0 right-0 text-center py-1 bg-black/70 rounded-t-lg">
        <p className="text-xs text-white">
          <span className="font-semibold">Trick #{trickNumber}</span>
          {' '}&mdash;{' '}
          Won by <span className="font-semibold text-yellow-400">{positionNames[trick.winner]}</span>
        </p>
      </div>

      {/* Compass layout: North (top), East (right), South (bottom), West (left) */}
      <div className="relative w-full h-full flex items-center justify-center">
        {/* North card - Top center */}
        {cardsByPosition.N && (
          <div className="absolute top-[6px] left-1/2 -translate-x-1/2">
            <TrickCard
              card={cardsByPosition.N}
              position="N"
              isWinner={trick.winner === 'N'}
            />
          </div>
        )}

        {/* East card - Right center */}
        {cardsByPosition.E && (
          <div className="absolute right-[16px] top-1/2 -translate-y-1/2">
            <TrickCard
              card={cardsByPosition.E}
              position="E"
              isWinner={trick.winner === 'E'}
            />
          </div>
        )}

        {/* South card - Bottom center */}
        {cardsByPosition.S && (
          <div className="absolute bottom-[6px] left-1/2 -translate-x-1/2">
            <TrickCard
              card={cardsByPosition.S}
              position="S"
              isWinner={trick.winner === 'S'}
            />
          </div>
        )}

        {/* West card - Left center */}
        {cardsByPosition.W && (
          <div className="absolute left-[16px] top-1/2 -translate-y-1/2">
            <TrickCard
              card={cardsByPosition.W}
              position="W"
              isWinner={trick.winner === 'W'}
            />
          </div>
        )}

        {/* Center indicator - smaller and more subtle */}
        <div className="text-white/70 text-[10px] bg-black/30 px-1.5 py-0.5 rounded">
          tap to close
        </div>
      </div>
    </div>
  );
}
