import React from 'react';
import { SUIT_SYMBOLS, SUIT_ORDER, groupBySuit } from '../types/hand-types';
import './HandDiagram.css';

/**
 * HandDiagram - Displays a hand in compact text format for review screens
 *
 * @param {Object} props
 * @param {Array<{rank: string, suit: 'S'|'H'|'D'|'C'}>} props.cards - Array of cards
 * @param {boolean} [props.highlight=false] - Whether to show gold border (player's hand)
 */
const HandDiagram = ({ cards = [], highlight = false }) => {
  // Group cards by suit in display order (♠♥♣♦)
  const groupedCards = groupBySuit(cards);

  return (
    <div className={`hand-diagram${highlight ? ' highlight' : ''}`}>
      {SUIT_ORDER.map((suit) => {
        const suitCards = groupedCards[suit] || [];
        const ranksDisplay = suitCards.length > 0
          ? suitCards.map((card) => card.rank).join(' ')
          : '—';

        return (
          <div key={suit} className="suit-line">
            <span className={`suit-sym ${suit.toLowerCase()}`}>
              {SUIT_SYMBOLS[suit]}
            </span>
            <span className="ranks">{ranksDisplay}</span>
          </div>
        );
      })}
    </div>
  );
};

export default HandDiagram;
