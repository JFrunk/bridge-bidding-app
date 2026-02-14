/**
 * DDTableDisplay Component - Double Dummy Analysis Table
 *
 * Displays the DDS matrix showing maximum tricks for each declarer/strain combination.
 *
 * Features:
 * - Full modal overlay with centered positioning (z-index 1000)
 * - Two-column layout: 35% explanatory text left, 65% table right
 * - Grid lines for clear data separation
 * - Color-coded cells: Game (blue), Slam (purple), Grand (gold)
 * - Backdrop blur for visual separation
 * - Dismiss button (X) in top-right corner
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
 * DDTableDisplay - Double Dummy Analysis Table with Modal Overlay
 *
 * Props:
 * @param {Object} ddAnalysis - The DD analysis data containing dd_table and par
 * @param {Function} onDismiss - Callback when dismiss button is clicked
 * @param {boolean} asOverlay - Whether to render as modal overlay (default: true)
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
            <th className="dd-corner-cell"></th>
            {STRAINS.map(strain => (
              <th
                key={strain}
                className={`dd-header-cell ${isRedStrain(strain) ? 'red-suit' : ''}`}
              >
                {STRAIN_SYMBOLS[strain]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {POSITIONS.map(pos => (
            <tr key={pos}>
              <td className="dd-position-cell">{pos}</td>
              {STRAINS.map(strain => {
                const tricks = dd_table[pos]?.[strain] ?? '-';
                const level = getContractLevel(tricks, strain);
                return (
                  <td key={strain} className={`dd-value-cell level-${level}`}>
                    <span className="dd-trick-value">{tricks}</span>
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

  // Full modal overlay with two-column layout
  return (
    <div className="dd-modal-overlay" onClick={onDismiss}>
      <div className="dd-modal-content" onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="dd-modal-header">
          <h3 className="dd-modal-title">Possible Tricks (Double Dummy)</h3>
          {onDismiss && (
            <button
              className="dd-modal-close"
              onClick={onDismiss}
              aria-label="Close"
            >
              ×
            </button>
          )}
        </div>

        {showExplanation ? (
          <div className="dd-modal-body">
            {/* Left column: Explanatory text */}
            <div className="dd-explanation">
              <p>
                This matrix shows the maximum number of tricks each position
                can win for every possible trump suit, assuming perfect play
                by all four players (double dummy conditions).
              </p>
              <p className="dd-explanation-tip">
                Use this to evaluate whether your contract was mathematically sound.
              </p>

              {/* Color Legend */}
              <div className="dd-color-legend">
                <div className="dd-legend-item">
                  <span className="dd-legend-swatch level-game"></span>
                  <span>Game</span>
                </div>
                <div className="dd-legend-item">
                  <span className="dd-legend-swatch level-slam"></span>
                  <span>Small Slam</span>
                </div>
                <div className="dd-legend-item">
                  <span className="dd-legend-swatch level-grand"></span>
                  <span>Grand Slam</span>
                </div>
              </div>
            </div>

            {/* Right column: Table */}
            <div className="dd-table-wrapper">
              {renderTable()}
            </div>
          </div>
        ) : (
          <div className="dd-modal-body-compact">
            {renderTable()}
          </div>
        )}
      </div>
    </div>
  );
};

export default DDTableDisplay;
