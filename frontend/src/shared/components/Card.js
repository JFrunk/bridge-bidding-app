/**
 * Card Component
 *
 * Displays a single playing card with rank and suit.
 * Used by both bidding and play modules.
 *
 * Props:
 *   - rank: Card rank ('A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2')
 *   - suit: Card suit ('♠', '♥', '♦', '♣')
 *   - onClick: Optional click handler for card selection
 *   - selectable: Whether the card can be selected (default: false)
 *   - selected: Whether the card is currently selected (default: false)
 */
import React from 'react';
import './Card.css';

function Card({ rank, suit, onClick, selectable = false, selected = false }) {
  const suitColor = suit === '♥' || suit === '♦' ? 'suit-red' : 'suit-black';

  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[rank] || rank;

  const handleClick = () => {
    if (selectable && onClick) {
      onClick({ rank, suit });
    }
  };

  const className = `card ${selectable ? 'card-selectable' : ''} ${selected ? 'card-selected' : ''}`;

  return (
    <div className={className} onClick={handleClick}>
      <div className={`card-corner top-left ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{suit}</span>
      </div>
      <div className={`card-center ${suitColor}`}>
        <span className="suit-symbol-large">{suit}</span>
      </div>
      <div className={`card-corner bottom-right ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{suit}</span>
      </div>
    </div>
  );
}

export default Card;
