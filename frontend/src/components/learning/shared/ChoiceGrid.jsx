import React from 'react';
import PropTypes from 'prop-types';
import './ChoiceGrid.css';

/**
 * ChoiceGrid - Renders a grid of choice buttons for quiz-style questions
 *
 * Handles correct/wrong states after answer submission and colorizes
 * bridge suit symbols in choice labels.
 */
function ChoiceGrid({
  choices,
  selectedId = null,
  correctId = null,
  showResult = false,
  disabled = false,
  onSelect
}) {
  /**
   * Colorize suit symbols in a label string
   * Returns JSX with colored spans for suit symbols
   */
  const colorizeLabel = (label) => {
    if (!label) return label;

    const parts = [];
    let lastIndex = 0;

    // Match suit symbols
    const suitPattern = /([♠♣♥♦])/g;
    let match;

    while ((match = suitPattern.exec(label)) !== null) {
      // Add text before the symbol
      if (match.index > lastIndex) {
        parts.push(label.slice(lastIndex, match.index));
      }

      // Add the colored symbol
      const symbol = match[1];
      const isRed = symbol === '♥' || symbol === '♦';
      parts.push(
        <span
          key={match.index}
          className={isRed ? 'suit-red' : 'suit-black'}
        >
          {symbol}
        </span>
      );

      lastIndex = match.index + 1;
    }

    // Add remaining text
    if (lastIndex < label.length) {
      parts.push(label.slice(lastIndex));
    }

    return parts.length > 0 ? parts : label;
  };

  /**
   * Determine the CSS classes for a choice button
   */
  const getChoiceClasses = (choiceId) => {
    const classes = ['choice-btn'];

    if (disabled && !showResult) {
      classes.push('disabled');
    }

    if (showResult) {
      // Show result states
      if (choiceId === correctId) {
        classes.push('correct');
      } else if (choiceId === selectedId && selectedId !== correctId) {
        classes.push('wrong');
      } else {
        classes.push('disabled');
      }
    } else if (choiceId === selectedId) {
      classes.push('selected');
    }

    return classes.join(' ');
  };

  const handleClick = (choiceId) => {
    if (disabled || showResult) return;
    onSelect(choiceId);
  };

  const handleKeyDown = (event, choiceId) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick(choiceId);
    }
  };

  return (
    <div className="choice-grid" role="group" aria-label="Answer choices">
      {choices.map((choice) => (
        <button
          key={choice.id}
          className={getChoiceClasses(choice.id)}
          onClick={() => handleClick(choice.id)}
          onKeyDown={(e) => handleKeyDown(e, choice.id)}
          disabled={disabled || showResult}
          aria-pressed={selectedId === choice.id}
          aria-disabled={disabled || showResult}
          type="button"
        >
          {colorizeLabel(choice.label)}
        </button>
      ))}
    </div>
  );
}

ChoiceGrid.propTypes = {
  choices: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    })
  ).isRequired,
  selectedId: PropTypes.string,
  correctId: PropTypes.string,
  showResult: PropTypes.bool,
  disabled: PropTypes.bool,
  onSelect: PropTypes.func.isRequired,
};

export default ChoiceGrid;
