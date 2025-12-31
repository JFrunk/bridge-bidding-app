import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * CurrentTrickDisplay - Shows the current trick in progress
 * NEW LAYOUT: Compass/spatial layout (North/East/South/West positions)
 * Cards appear in front of player positions with bold border for winner
 * PRIMARY visual element during card play
 */
export function CurrentTrickDisplay({ trick, trickWinner, trickComplete }) {
  console.log('🃏 CurrentTrickDisplay received:', { trick, trick_length: trick?.length, trickWinner, trickComplete });

  // DEFENSIVE: Only show the first 4 cards (a complete trick)
  const displayTrick = trick?.slice(0, 4) || [];
  if (trick && trick.length > 4) {
    console.error('⚠️ WARNING: Trick has more than 4 cards!', {
      trick_length: trick.length,
      trick_data: trick
    });
  }

  const suitColor = (suit) => suit === '♥' || suit === '♦' ? 'text-suit-red' : 'text-suit-black';
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };

  // Create a map of position -> card
  const cardsByPosition = {};
  displayTrick.forEach(({ card, position }) => {
    cardsByPosition[position] = card;
  });

  // Card component for trick display - compact top-left corner only
  const TrickCard = ({ card, position, isWinner }) => {
    if (!card) return null;

    const displayRank = rankMap[card.rank] || card.rank;

    return (
      <div
        className={cn(
          "trick-card relative bg-white rounded-card shadow-md pointer-events-auto",
          "transition-all duration-500",
          // Bold border (ring) for winner
          isWinner ? "ring-4 ring-white shadow-2xl border-0" : "border border-gray-400",
          // Slight scale up for winner
          isWinner && "scale-105"
        )}
      >
        {/* Top-left corner only - matches PlayableCard/BridgeCard style */}
        <div className={cn("absolute top-1 left-1.5 leading-none flex flex-col items-center", suitColor(card.suit))}>
          <span className="text-lg font-bold">{displayRank}</span>
          <span className="text-base">{card.suit}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="relative flex items-center justify-center w-full h-full min-h-[350px] pointer-events-none">
      {displayTrick.length === 0 ? (
        // Waiting for cards message
        <div className="flex items-center justify-center p-12 rounded-lg border-2 border-dashed border-gray-600 bg-bg-secondary pointer-events-auto">
          <p className="text-base text-gray-400">Waiting for cards...</p>
        </div>
      ) : (
        // Compass layout: North (top), East (right), South (bottom), West (left)
        <div className="relative w-full h-full flex items-center justify-center">
          {/* North card - Top center */}
          {cardsByPosition.N && (
            <div className="absolute top-0 left-1/2 -translate-x-1/2">
              <TrickCard
                card={cardsByPosition.N}
                position="N"
                isWinner={trickComplete && trickWinner === 'N'}
              />
            </div>
          )}

          {/* East card - Right center */}
          {cardsByPosition.E && (
            <div className="absolute right-0 top-1/2 -translate-y-1/2">
              <TrickCard
                card={cardsByPosition.E}
                position="E"
                isWinner={trickComplete && trickWinner === 'E'}
              />
            </div>
          )}

          {/* South card - Bottom center */}
          {cardsByPosition.S && (
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2">
              <TrickCard
                card={cardsByPosition.S}
                position="S"
                isWinner={trickComplete && trickWinner === 'S'}
              />
            </div>
          )}

          {/* West card - Left center */}
          {cardsByPosition.W && (
            <div className="absolute left-0 top-1/2 -translate-y-1/2">
              <TrickCard
                card={cardsByPosition.W}
                position="W"
                isWinner={trickComplete && trickWinner === 'W'}
              />
            </div>
          )}

          {/* Center "Waiting" text (only visible when cards < 4) */}
          {displayTrick.length < 4 && (
            <div className="text-gray-500 text-sm">
              Waiting for cards...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
