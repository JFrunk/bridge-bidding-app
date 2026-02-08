/**
 * HandDisplay Component
 * Renders a bridge hand as overlapping cards with content positioned in the visible left strip.
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

import React from 'react';
import PropTypes from 'prop-types';
import { SUIT_SYMBOLS, isRedSuit, sortCards } from '../types/hand-types';
import './HandDisplay.css';

/**
 * @param {Object} props
 * @param {Array<{rank: string, suit: 'S'|'H'|'D'|'C'}>} props.cards - Array of cards to display
 * @param {'hand-h' | 'suit-row' | 'hand-mini'} props.mode - Display mode (default: 'hand-h')
 * @param {boolean} props.selectable - Whether cards can be selected
 * @param {number} props.selectedIndex - Currently selected card index
 * @param {number} props.correctIndex - Index of correct card (for feedback)
 * @param {number} props.incorrectIndex - Index of incorrect card (for feedback)
 * @param {number[]} props.disabledIndices - Indices of disabled cards
 * @param {function} props.onCardClick - (index) => void
 */
function HandDisplay({
  cards = [],
  mode = 'hand-h',
  selectable = false,
  selectedIndex = -1,
  correctIndex = -1,
  incorrectIndex = -1,
  disabledIndices = [],
  onCardClick,
}) {
  // Sort cards by suit (S H C D) then by rank (high to low)
  const sortedCards = sortCards(cards);

  const handleCardClick = (index) => {
    if (!selectable) return;
    if (disabledIndices.includes(index)) return;
    if (onCardClick) {
      onCardClick(index);
    }
  };

  const handleKeyDown = (event, index) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleCardClick(index);
    }
  };

  return (
    <div className={`hand-display hand-display--${mode}`}>
      {sortedCards.map((card, index) => {
        const isRed = isRedSuit(card.suit);
        const isSelected = index === selectedIndex;
        const isCorrect = index === correctIndex;
        const isIncorrect = index === incorrectIndex;
        const isDisabled = disabledIndices.includes(index);

        const cardClasses = [
          'hand-card',
          isRed ? 'red' : 'black',
          selectable && !isDisabled ? 'selectable' : '',
          isSelected ? 'selected' : '',
          isCorrect ? 'correct' : '',
          isIncorrect ? 'incorrect' : '',
          isDisabled ? 'disabled' : '',
        ]
          .filter(Boolean)
          .join(' ');

        return (
          <div
            key={`${card.rank}-${card.suit}-${index}`}
            className={cardClasses}
            onClick={() => handleCardClick(index)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            tabIndex={selectable && !isDisabled ? 0 : -1}
            role={selectable ? 'button' : undefined}
            aria-pressed={selectable ? isSelected : undefined}
            aria-disabled={isDisabled}
            aria-label={`${card.rank} of ${SUIT_SYMBOLS[card.suit]}`}
          >
            <div className="hand-card-content">
              <span className="hand-card-rank">{card.rank}</span>
              <span className="hand-card-suit">{SUIT_SYMBOLS[card.suit]}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

HandDisplay.propTypes = {
  cards: PropTypes.arrayOf(
    PropTypes.shape({
      rank: PropTypes.string.isRequired,
      suit: PropTypes.oneOf(['S', 'H', 'D', 'C']).isRequired,
    })
  ),
  mode: PropTypes.oneOf(['hand-h', 'suit-row', 'hand-mini']),
  selectable: PropTypes.bool,
  selectedIndex: PropTypes.number,
  correctIndex: PropTypes.number,
  incorrectIndex: PropTypes.number,
  disabledIndices: PropTypes.arrayOf(PropTypes.number),
  onCardClick: PropTypes.func,
};

export default HandDisplay;
