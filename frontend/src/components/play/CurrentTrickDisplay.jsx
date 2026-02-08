import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * CurrentTrickDisplay - Shows the current trick in progress
 * NEW LAYOUT: Compass/spatial layout (North/East/South/West positions)
 * Cards appear in front of player positions with bold border for winner
 * PRIMARY visual element during card play
 */
export function CurrentTrickDisplay({ trick, trickWinner, trickComplete, nextToPlay }) {
  console.log('🃏 CurrentTrickDisplay received:', { trick, trick_length: trick?.length, trickWinner, trickComplete, nextToPlay });

  // Map position codes to full names
  const positionNames = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };
  const nextPlayerName = positionNames[nextToPlay] || nextToPlay;

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

  // Card component for trick display - compact per UI Redesign Spec
  const TrickCard = ({ card, position, isWinner }) => {
    if (!card) return null;

    const displayRank = rankMap[card.rank] || card.rank;

    return (
      <div
        className={cn(
          "trick-card pointer-events-auto",
          "transition-all duration-300",
          // Gold border for winner per spec
          isWinner && "winner"
        )}
      >
        {/* Centered rank and suit */}
        <span className={cn("rank", suitColor(card.suit))}>{displayRank}</span>
        <span className={cn("suit", suitColor(card.suit))}>{card.suit}</span>
      </div>
    );
  };

  return (
    <div className="current-trick">
      {displayTrick.length === 0 ? (
        // Show who should play next - uses empty state styling
        <div className="trick-label">
          {nextToPlay ? `${nextPlayerName} to lead...` : 'Waiting...'}
        </div>
      ) : (
        // Compass layout using CSS grid areas
        <>
          {/* North card */}
          <div className="trick-card-north">
            {cardsByPosition.N && (
              <TrickCard
                card={cardsByPosition.N}
                position="N"
                isWinner={trickComplete && trickWinner === 'N'}
              />
            )}
          </div>

          {/* West card */}
          <div className="trick-card-west">
            {cardsByPosition.W && (
              <TrickCard
                card={cardsByPosition.W}
                position="W"
                isWinner={trickComplete && trickWinner === 'W'}
              />
            )}
          </div>

          {/* Center label REMOVED per CC_CORRECTIONS Fix #6
              The "{position}..." text was a rendering artifact.
              Turn indicator below the table already shows whose turn it is. */}

          {/* East card */}
          <div className="trick-card-east">
            {cardsByPosition.E && (
              <TrickCard
                card={cardsByPosition.E}
                position="E"
                isWinner={trickComplete && trickWinner === 'E'}
              />
            )}
          </div>

          {/* South card */}
          <div className="trick-card-south">
            {cardsByPosition.S && (
              <TrickCard
                card={cardsByPosition.S}
                position="S"
                isWinner={trickComplete && trickWinner === 'S'}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
