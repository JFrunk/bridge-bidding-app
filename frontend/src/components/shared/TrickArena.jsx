/**
 * TrickArena - "Spacious Cross" Central Arena
 * Physics v2.0 compliant - all dimensions in em units
 *
 * Displays played cards from all 4 positions with:
 * - Zero overlap between cards
 * - Cards remain in designated slots showing play order
 * - Winner highlighting with gold border
 * - No position labels (already shown on the surrounding table)
 */
import React from 'react';
import Card from '../../shared/components/Card';

const TrickArena = ({ playedCards = {}, scaleClass = "text-base" }) => {
  // playedCards expected format: { N: {rank, suit, isWinner?}, E: ..., S: ..., W: ... }

  const Position = ({ seat, card }) => {
    const isWinner = card?.isWinner;

    return (
      <div className={`absolute flex flex-col items-center w-[4em] ${
        seat === 'N' ? 'top-[1em] left-1/2 -translate-x-1/2' :
        seat === 'S' ? 'bottom-[1em] left-1/2 -translate-x-1/2' :
        seat === 'W' ? 'top-1/2 left-[1em] -translate-y-1/2' :
        'top-1/2 right-[1em] -translate-y-1/2'
      }`}>
        <div className={`w-[3.5em] h-[5.0em] rounded-[0.35em] flex items-center justify-center ${
          isWinner
            ? 'ring-[0.15em] ring-amber-400 shadow-[0_0_0.5em_rgba(251,191,36,0.5)]'
            : 'border-[0.1em] border-white/10'
        }`}>
          {card ? (
            <Card rank={card.rank} suit={card.suit} customScaleClass={scaleClass} />
          ) : (
            <div className="w-full h-full bg-black/5 rounded-[0.35em]" />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`${scaleClass} relative w-[22em] h-[20em] bg-black/5 border-[0.1em] border-dashed border-white/10 rounded-[1em]`}>
      <Position seat="N" card={playedCards.N} />
      <Position seat="W" card={playedCards.W} />
      <Position seat="E" card={playedCards.E} />
      <Position seat="S" card={playedCards.S} />
    </div>
  );
};

export default TrickArena;
