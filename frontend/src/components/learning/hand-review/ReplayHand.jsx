/**
 * ReplayHand - Shared card display components for review pages
 *
 * Used by both BidReviewPage (bidding walkthrough) and HandReviewPage (play walkthrough).
 * Accepts optional trumpStrain for play review (defaults to null for bidding).
 */

import React, { useMemo } from 'react';
import Card from '../../../shared/components/Card';
import {
  getSuitOrder,
  groupCardsBySuit,
  sortCards
} from './constants';

/**
 * ReplayHorizontalHand - Horizontal hand layout for N/S positions
 */
export const ReplayHorizontalHand = ({ cards, position, trumpStrain = null, scaleClass = 'text-base', isUser = false }) => {
  const suitOrder = getSuitOrder(trumpStrain);
  const cardsBySuit = useMemo(() => {
    const grouped = groupCardsBySuit(cards);
    Object.keys(grouped).forEach(suit => {
      grouped[suit] = sortCards(grouped[suit]);
    });
    return grouped;
  }, [cards]);

  const getSpacingClass = (count) => {
    if (count >= 7) return '-space-x-[2.2em]';
    if (count === 6) return '-space-x-[1.9em]';
    if (count === 5) return '-space-x-[1.6em]';
    return '-space-x-[1.4em]';
  };

  const positionLabels = { N: 'North', S: 'South' };

  if (!cards || cards.length === 0) {
    return (
      <div className={`${scaleClass} text-center text-white/60 py-4`}>
        No cards
      </div>
    );
  }

  return (
    <div className={`${scaleClass} flex flex-col items-center gap-[0.3em]`}>
      <div className="text-[0.75em] font-semibold text-white/70 uppercase tracking-wider flex items-center gap-2">
        {positionLabels[position]}
        {isUser && (
          <span className="bg-blue-500 text-white px-2 py-0.5 rounded-full text-[0.7em] normal-case">
            You
          </span>
        )}
      </div>
      <div className="flex flex-row gap-[0.8em] justify-center">
        {suitOrder.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (!suitCards || suitCards.length === 0) return null;
          const spacingClass = getSpacingClass(suitCards.length);

          return (
            <div key={suit} className={`flex flex-row ${spacingClass}`}>
              {suitCards.map((card, idx) => (
                <div key={`${card.rank}-${card.suit}`} style={{ zIndex: 10 + idx }}>
                  <Card
                    rank={card.rank}
                    suit={card.suit}
                    customScaleClass={scaleClass}
                  />
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

/**
 * ReplaySuitStack - Vertical suit stack layout for E/W positions
 */
export const ReplaySuitStack = ({ cards, position, trumpStrain = null, scaleClass = 'text-sm' }) => {
  const suitOrder = getSuitOrder(trumpStrain);
  const cardsBySuit = useMemo(() => {
    const grouped = groupCardsBySuit(cards);
    Object.keys(grouped).forEach(suit => {
      grouped[suit] = sortCards(grouped[suit]);
    });
    return grouped;
  }, [cards]);

  const getSpacingClass = (count) => {
    if (count >= 7) return '-space-x-[1.9em]';
    if (count === 6) return '-space-x-[1.6em]';
    if (count === 5) return '-space-x-[1.4em]';
    return '-space-x-[1.2em]';
  };

  const positionLabels = { E: 'East', W: 'West' };

  if (!cards || cards.length === 0) {
    return (
      <div className={`${scaleClass} text-center text-white/60 py-4`}>
        No cards
      </div>
    );
  }

  return (
    <div className={`${scaleClass} flex flex-col items-center gap-[0.3em]`}>
      <div className="text-[0.75em] font-semibold text-white/70 uppercase tracking-wider">
        {positionLabels[position]}
      </div>
      <div className="flex flex-col gap-[0.3em]">
        {suitOrder.map(suit => {
          const suitCards = cardsBySuit[suit];
          if (!suitCards || suitCards.length === 0) return null;
          const spacingClass = getSpacingClass(suitCards.length);

          return (
            <div key={suit} className={`flex flex-row ${spacingClass}`}>
              {suitCards.map((card, idx) => (
                <div key={`${card.rank}-${card.suit}`} style={{ zIndex: 10 + idx }}>
                  <Card
                    rank={card.rank}
                    suit={card.suit}
                    customScaleClass={scaleClass}
                  />
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};
