import * as React from "react";
import TrickArena from "../shared/TrickArena";
import { toVisualSeat, SEAT_NAMES } from "../../utils/seats";

/**
 * CurrentTrickDisplay - Shows the current trick in progress
 * Uses TrickArena "Spacious Cross" layout (Physics v2.0)
 *
 * Features:
 * - Zero overlap between cards
 * - Cards remain in designated slots for play order attribution
 * - Position-relative rendering: viewer always at bottom
 * - All dimensions in em units for scalability
 */
export function CurrentTrickDisplay({ trick, trickWinner, trickComplete, nextToPlay, userPosition = 'S' }) {
  // Map position codes to full names for the waiting message
  const nextPlayerName = SEAT_NAMES[nextToPlay] || nextToPlay;

  // DEFENSIVE: Only show the first 4 cards (a complete trick)
  const displayTrick = trick?.slice(0, 4) || [];

  // Convert trick array to position map for TrickArena
  // TrickArena expects: { N: {rank, suit}, E: {...}, S: {...}, W: {...} }
  // Transform absolute positions to visual positions so the viewer is always at bottom
  const playedCards = {};
  displayTrick.forEach(({ card, position }) => {
    if (card && position) {
      const visualPos = toVisualSeat(position, userPosition);
      playedCards[visualPos] = {
        rank: card.rank,
        suit: card.suit,
        isWinner: trickComplete && trickWinner === position
      };
    }
  });

  // Empty state - show who leads next
  if (displayTrick.length === 0) {
    return (
      <div className="text-sm relative w-[22em] h-[20em] bg-black/5 border-[0.1em] border-dashed border-white/10 rounded-[1em] flex items-center justify-center">
        <span className="text-[1.2em] font-medium text-white/60">
          {nextToPlay ? `${nextPlayerName} to lead...` : 'Waiting...'}
        </span>
      </div>
    );
  }

  return <TrickArena playedCards={playedCards} scaleClass="text-sm" />;
}
