/**
 * LearningCard Component
 *
 * A visual card display for learning mode that matches the main app's styling.
 * Uses a white background with proper red/black suit colors for easy recognition.
 *
 * @param {Object} props
 * @param {string} props.rank - Card rank: 'A', 'K', 'Q', 'J', 'T' (10), '9', etc.
 * @param {string} props.suit - Card suit: '♠', '♥', '♦', '♣'
 * @param {string} props.className - Additional CSS classes
 */
import React from 'react';
import './LearningCard.css';

export function LearningCard({ rank, suit, className = '' }) {
  // Determine suit color (red for hearts/diamonds, black for spades/clubs)
  const isRed = suit === '♥' || suit === '♦';
  const colorClass = isRed ? 'card-red' : 'card-black';

  // Map 'T' to '10' for display
  const displayRank = rank === 'T' ? '10' : rank;

  return (
    <div className={`learning-card ${colorClass} ${className}`}>
      {/* Top-left corner */}
      <div className="card-corner top-left">
        <span className="card-rank">{displayRank}</span>
        <span className="card-suit">{suit}</span>
      </div>

      {/* Center suit */}
      <div className="card-center">
        <span className="card-suit-large">{suit}</span>
      </div>

      {/* Bottom-right corner (rotated) */}
      <div className="card-corner bottom-right">
        <span className="card-rank">{displayRank}</span>
        <span className="card-suit">{suit}</span>
      </div>
    </div>
  );
}

/**
 * LearningHand Component
 *
 * Displays a full hand of cards organized by suit.
 * Matches the main app's hand display style.
 *
 * @param {Object} props
 * @param {Array} props.cards - Array of {rank, suit} objects
 */
export function LearningHand({ cards }) {
  if (!cards || !Array.isArray(cards) || cards.length === 0) {
    return <div className="learning-hand empty">No cards</div>;
  }

  // Order suits: ♠, ♥, ♦, ♣
  const suitOrder = ['♠', '♥', '♦', '♣'];

  // Group cards by suit
  const cardsBySuit = suitOrder.map(suit => ({
    suit,
    cards: cards.filter(card => card.suit === suit)
  })).filter(group => group.cards.length > 0);

  return (
    <div className="learning-hand">
      {cardsBySuit.map(({ suit, cards: suitCards }) => (
        <div key={suit} className="suit-group">
          {suitCards.map((card, index) => (
            <LearningCard
              key={`${card.rank}-${card.suit}-${index}`}
              rank={card.rank}
              suit={card.suit}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export default LearningCard;
