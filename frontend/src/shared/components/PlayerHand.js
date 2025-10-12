/**
 * PlayerHand Component
 *
 * Displays a player's hand with cards organized by suit.
 * Used by both bidding and play modules.
 *
 * Props:
 *   - position: Player position ('N', 'E', 'S', 'W' or 'North', 'East', 'South', 'West')
 *   - hand: Array of card objects [{ rank, suit }, ...]
 *   - points: Hand analysis object (optional)
 *   - vulnerability: Vulnerability string (optional)
 *   - trumpSuit: Trump suit for ordering (null for NT, default: null)
 *   - onCardClick: Callback when card is clicked (optional)
 *   - selectableCards: Array of selectable card indices (optional)
 *   - selectedCards: Array of selected card objects (optional)
 *   - showAnalysis: Whether to show hand analysis (default: true)
 *   - compactAnalysis: Whether to use compact analysis view (default: false)
 */
import React from 'react';
import Card from './Card';
import HandAnalysis from './HandAnalysis';
import { getSuitOrder } from '../utils/cardUtils';
import './PlayerHand.css';

function PlayerHand({
  position,
  hand,
  points,
  vulnerability,
  trumpSuit = null,
  onCardClick,
  selectableCards = [],
  selectedCards = [],
  showAnalysis = true,
  compactAnalysis = false
}) {
  if (!hand) return null;

  const suitOrder = getSuitOrder(trumpSuit);

  const isCardSelected = (card) => {
    return selectedCards.some(
      selected => selected.rank === card.rank && selected.suit === card.suit
    );
  };

  const isCardSelectable = (index) => {
    return selectableCards.length === 0 || selectableCards.includes(index);
  };

  return (
    <div className={`player-hand player-${position.toLowerCase()}`}>
      <h3>{position}</h3>
      <div className="hand-display">
        {suitOrder.map(suit => (
          <div key={suit} className="suit-group">
            {hand
              .map((card, index) => ({ card, index }))
              .filter(({ card }) => card.suit === suit)
              .map(({ card, index }) => (
                <Card
                  key={`${suit}-${index}`}
                  rank={card.rank}
                  suit={card.suit}
                  onClick={onCardClick}
                  selectable={isCardSelectable(index)}
                  selected={isCardSelected(card)}
                />
              ))}
          </div>
        ))}
      </div>
      {showAnalysis && points && (
        <HandAnalysis
          points={points}
          vulnerability={vulnerability}
          compact={compactAnalysis}
        />
      )}
    </div>
  );
}

export default PlayerHand;
