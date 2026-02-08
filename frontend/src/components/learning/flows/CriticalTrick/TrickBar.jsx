/**
 * TrickBar Component
 * 13-cell horizontal bar showing trick status for declarer play
 *
 * Each cell represents one trick (1-13) with different states:
 * - .won-ns (green) - Trick won by North-South
 * - .won-ew (red) - Trick won by East-West
 * - .current (white border) - Current trick being played
 * - .target (gold underline) - Target trick needed to make contract
 */

import React from 'react';
import PropTypes from 'prop-types';
import './CriticalTrick.css';

/**
 * @param {Object} props
 * @param {number} props.tricksWonNS - Tricks won by declarer (NS)
 * @param {number} props.tricksWonEW - Tricks won by defense (EW)
 * @param {number} props.tricksNeeded - Total tricks declarer needs
 * @param {number} props.currentTrick - Which trick we're on (1-13)
 */
function TrickBar({
  tricksWonNS = 0,
  tricksWonEW = 0,
  tricksNeeded = 0,
  currentTrick = 0
}) {
  // Build the 13 trick cells
  const tricks = [];

  for (let i = 1; i <= 13; i++) {
    const tricksPlayedSoFar = tricksWonNS + tricksWonEW;

    let cellClass = 'trick-cell';

    // Determine if this trick has been won and by whom
    if (i <= tricksWonNS) {
      // This represents an NS win (first N tricks won by NS)
      cellClass += ' won-ns';
    } else if (i <= tricksPlayedSoFar) {
      // This represents an EW win
      cellClass += ' won-ew';
    }

    // Current trick indicator
    if (i === tricksPlayedSoFar + 1 || (tricksPlayedSoFar === 0 && i === 1)) {
      if (currentTrick === i || (currentTrick === 0 && i === tricksPlayedSoFar + 1)) {
        cellClass += ' current';
      }
    }

    // Target trick (the trick needed to make contract)
    if (i === tricksNeeded) {
      cellClass += ' target';
    }

    tricks.push(
      <div
        key={i}
        className={cellClass}
        aria-label={`Trick ${i}${i <= tricksWonNS ? ' won by declarer' : i <= tricksPlayedSoFar ? ' won by defense' : ' not played'}`}
      >
        <span className="trick-number">{i}</span>
      </div>
    );
  }

  return (
    <div className="trick-bar" role="img" aria-label={`Trick progress: Declarer ${tricksWonNS}, Defense ${tricksWonEW}`}>
      <div className="trick-bar-cells">
        {tricks}
      </div>
      <div className="trick-bar-legend">
        <span className="legend-item">
          <span className="legend-dot won-ns"></span>
          <span className="legend-label">Declarer</span>
        </span>
        <span className="legend-item">
          <span className="legend-dot won-ew"></span>
          <span className="legend-label">Defense</span>
        </span>
        <span className="legend-item">
          <span className="legend-dot target"></span>
          <span className="legend-label">Need {tricksNeeded}</span>
        </span>
      </div>
    </div>
  );
}

TrickBar.propTypes = {
  tricksWonNS: PropTypes.number,
  tricksWonEW: PropTypes.number,
  tricksNeeded: PropTypes.number,
  currentTrick: PropTypes.number
};

export default TrickBar;
