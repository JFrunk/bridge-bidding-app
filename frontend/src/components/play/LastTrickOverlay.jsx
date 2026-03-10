import * as React from "react";
import { cn } from "../../lib/utils";
import { toVisualSeat, SEAT_NAMES } from "../../utils/seats";
import { isRedSuit } from "../../utils/suitColors";

/**
 * LastTrickOverlay - Shows the last completed trick in compass layout
 *
 * Displays when user clicks "Last Trick" button, auto-dismisses after 3 seconds.
 * Uses same card layout as CurrentTrickDisplay for visual consistency.
 * Position-relative rendering: viewer always at bottom.
 *
 * CRITICAL: Uses inline styles for colors to ensure visibility regardless of Tailwind config
 */
export function LastTrickOverlay({ trick, trickNumber, onClose, userPosition = 'S' }) {
  if (!trick || !trick.cards) return null;

  // Use inline styles for guaranteed color visibility (not Tailwind classes)
  const getSuitStyle = (suit) => ({
    color: isRedSuit(suit) ? '#d32f2f' : '#000000'  // Red or black
  });
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };

  // Create a map of visual position -> card from trick data
  // Transform absolute positions to visual positions so the viewer is always at bottom
  const cardsByPosition = {};
  trick.cards.forEach(({ card, position }) => {
    const visualPos = toVisualSeat(position, userPosition);
    cardsByPosition[visualPos] = card;
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

  // Transform winner to visual position for highlighting
  const visualWinner = trick.winner ? toVisualSeat(trick.winner, userPosition) : null;

  return (
    <div
      className="relative flex flex-col items-center justify-center w-[200px] h-[180px] cursor-pointer mx-auto"
      onClick={onClose}
      title="Click to dismiss"
    >
      {/* Header showing trick number and winner (display absolute name) */}
      <div className="absolute -top-6 left-0 right-0 text-center py-1 bg-black/70 rounded-t-lg">
        <p className="text-xs text-white">
          <span className="font-semibold">Trick #{trickNumber}</span>
          {' '}&mdash;{' '}
          Won by <span className="font-semibold text-yellow-400">{SEAT_NAMES[trick.winner]}</span>
        </p>
      </div>

      {/* Compass layout: positions are visual (viewer at bottom=S) */}
      <div className="relative w-full h-full flex items-center justify-center">
        {/* Top center (partner) */}
        {cardsByPosition.N && (
          <div className="absolute top-[6px] left-1/2 -translate-x-1/2">
            <TrickCard
              card={cardsByPosition.N}
              position="N"
              isWinner={visualWinner === 'N'}
            />
          </div>
        )}

        {/* Right center (RHO) */}
        {cardsByPosition.E && (
          <div className="absolute right-[16px] top-1/2 -translate-y-1/2">
            <TrickCard
              card={cardsByPosition.E}
              position="E"
              isWinner={visualWinner === 'E'}
            />
          </div>
        )}

        {/* Bottom center (viewer) */}
        {cardsByPosition.S && (
          <div className="absolute bottom-[6px] left-1/2 -translate-x-1/2">
            <TrickCard
              card={cardsByPosition.S}
              position="S"
              isWinner={visualWinner === 'S'}
            />
          </div>
        )}

        {/* Left center (LHO) */}
        {cardsByPosition.W && (
          <div className="absolute left-[16px] top-1/2 -translate-y-1/2">
            <TrickCard
              card={cardsByPosition.W}
              position="W"
              isWinner={visualWinner === 'W'}
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
