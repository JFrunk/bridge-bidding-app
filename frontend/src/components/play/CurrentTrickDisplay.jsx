import * as React from "react";
import TrickArena from "../shared/TrickArena";

/**
 * CurrentTrickDisplay - Shows the current trick in progress
 * Uses TrickArena "Spacious Cross" layout (Physics v2.0)
 *
 * Features:
 * - Zero overlap between cards
 * - Clear position labels (N/E/S/W)
 * - Cards remain in designated slots for play order attribution
 * - All dimensions in em units for scalability
 */
export function CurrentTrickDisplay({ trick, trickWinner, trickComplete, nextToPlay }) {
  // Map position codes to full names for the waiting message
  const positionNames = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
  const nextPlayerName = positionNames[nextToPlay] || nextToPlay;

  // DEFENSIVE: Only show the first 4 cards (a complete trick)
  const displayTrick = trick?.slice(0, 4) || [];

  // Convert trick array to position map for TrickArena
  // TrickArena expects: { N: {rank, suit}, E: {...}, S: {...}, W: {...} }
  const playedCards = {};
  displayTrick.forEach(({ card, position }) => {
    if (card && position) {
      playedCards[position] = {
        rank: card.rank,
        suit: card.suit,
        isWinner: trickComplete && trickWinner === position
      };
    }
  });

  // Empty state - show who leads next
  if (displayTrick.length === 0) {
    return (
      <div className="text-base relative w-[22em] h-[20em] bg-black/5 border-[0.1em] border-dashed border-white/10 rounded-[1em] flex items-center justify-center">
        <span className="text-[1.2em] font-medium text-white/60">
          {nextToPlay ? `${nextPlayerName} to lead...` : 'Waiting...'}
        </span>
      </div>
    );
  }

  return <TrickArena playedCards={playedCards} scaleClass="text-base" />;
}
