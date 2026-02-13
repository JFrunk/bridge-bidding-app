/**
 * DDTableDisplay Component - Double Dummy Analysis Table
 *
 * Displays the DDS matrix showing maximum tricks for each declarer/strain combination.
 *
 * Features:
 * - Overlay layering (z-index 999) ensures table appears ABOVE cards/game assets
 * - Two-column layout: 30% explanatory text left, 70% table right
 * - Backdrop blur for visual separation
 * - Dismiss button (X) in top-right corner
 * - Color coding for game/slam/grand levels
 * - Responsive scaling with vmin units
 */

import React from 'react';
import './DDTableDisplay.css';

// Strain display configuration
const STRAINS = ['NT', 'S', 'H', 'D', 'C'];
const STRAIN_SYMBOLS = {
  NT: 'NT',
  S: '\u2660',  // ♠
  H: '\u2665',  // ♥
  D: '\u2666',  // ♦
  C: '\u2663'   // ♣
};
const POSITIONS = ['N', 'S', 'E', 'W'];

/**
 * Determine contract level for color coding
 */
const getContractLevel = (tricks, strain) => {
  if (typeof tricks !== 'number') return 'partscore';
  if (tricks >= 13) return 'grand';
  if (tricks >= 12) return 'slam';

  const isMinor = strain === 'C' || strain === 'D';
  const isMajor = strain === 'S' || strain === 'H';

  if (strain === 'NT' && tricks >= 9) return 'game';
  if (isMajor && tricks >= 10) return 'game';
  if (isMinor && tricks >= 11) return 'game';

  return 'partscore';
};

/**
 * Check if strain is red (hearts or diamonds)
 */
const isRedStrain = (strain) => strain === 'H' || strain === 'D';

/**
 * DDTableDisplay - Double Dummy Analysis Table with Overlay
 *
 * Props:
 * @param {Object} ddAnalysis - The DD analysis data containing dd_table and par
 * @param {Function} onDismiss - Callback when dismiss button is clicked
 * @param {boolean} asOverlay - Whether to render as overlay (default: true)
 * @param {boolean} showExplanation - Whether to show two-column layout with text (default: true)
 */
const DDTableDisplay = ({
  ddAnalysis,
  onDismiss,
  asOverlay = true,
  showExplanation = true
}) => {
  if (!ddAnalysis?.dd_table) return null;

  const { dd_table, par } = ddAnalysis;

  // Render the table itself
  const renderTable = () => (
    <div className="dd-table-container">
      <table className="dd-table">
        <thead>
          <tr>
            <th></th>
            {STRAINS.map(strain => (
              <th
                key={strain}
                className={isRedStrain(strain) ? 'red-suit' : ''}
              >
                {STRAIN_SYMBOLS[strain]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {POSITIONS.map(pos => (
            <tr key={pos}>
              <td className="position-header">{pos}</td>
              {STRAINS.map(strain => {
                const tricks = dd_table[pos]?.[strain] ?? '-';
                const level = getContractLevel(tricks, strain);
                const levelClass = level === 'game' ? 'level-game' :
                                   level === 'slam' ? 'level-slam' :
                                   level === 'grand' ? 'level-grand' : '';
                return (
                  <td key={strain} className={levelClass}>
                    {tricks}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Par display */}
      {par && (
        <div className="dd-table-par">
          <span className="par-label">Par: </span>
          <span className="par-value">
            {par.contracts?.join(' / ') || 'Unknown'}
            {par.score !== undefined && ` (${par.score >= 0 ? '+' : ''}${par.score})`}
          </span>
        </div>
      )}
    </div>
  );

  // Simple table without overlay
  if (!asOverlay) {
    return renderTable();
  }

  // Full overlay with two-column layout
  return (
    <div className="dd-table-overlay">
      {/* Dismiss button */}
      {onDismiss && (
        <button
          className="dd-table-dismiss"
          onClick={onDismiss}
          aria-label="Dismiss DD table"
        >
          ×
        </button>
      )}

      {showExplanation ? (
        <div className="dd-table-two-column">
          {/* Left column: Explanatory text (30%) */}
          <div className="dd-table-explanation">
            <h3>Possible Tricks (Double Dummy)</h3>
            <p>
              This matrix represents the theoretical maximum number of tricks each
              position can win for every possible strain. These values assume
              "Double Dummy" conditions—where all players see all cards and play
              perfectly. Use this to benchmark if your contract was mathematically sound.
            </p>
            <div className="explanation-tip">
              <div className="color-legend">
                <span className="legend-game">Blue = Game</span>
                <span className="legend-slam">Purple = Slam</span>
                <span className="legend-grand">Yellow = Grand</span>
              </div>
            </div>
          </div>

          {/* Right column: Table (70%) */}
          <div className="dd-table-main">
            {renderTable()}
          </div>
        </div>
      ) : (
        <div className="dd-table-main" style={{ padding: '16px' }}>
          {renderTable()}
        </div>
      )}
    </div>
  );
};

export default DDTableDisplay;
