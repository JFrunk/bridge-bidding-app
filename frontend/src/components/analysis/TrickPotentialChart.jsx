import * as React from "react";
import ChartHelp from '../help/ChartHelp';
import "./TrickPotentialChart.css";

/**
 * TrickPotentialChart - Shows double-dummy trick potential for NS/EW
 *
 * Displays a compact table showing how many tricks each side can make
 * in each strain (NT, ♠, ♥, ♦, ♣) with subtle color-coded borders:
 * - Green: Game (NT: 9+, Major: 10+, Minor: 11+)
 * - Orange: Small Slam (12)
 * - Red: Grand Slam (13)
 *
 * Props:
 *   - ddTable: Object with NS/EW trick counts { NS: {NT, S, H, D, C}, EW: {NT, S, H, D, C} }
 *   - onClose: Function to close the overlay (optional)
 *   - compact: Boolean for inline display without overlay
 */

// Strain display order and symbols
const STRAINS = [
  { key: 'NT', symbol: 'NT', isMinor: false, isMajor: false },
  { key: 'S', symbol: '♠', isMinor: false, isMajor: true },
  { key: 'H', symbol: '♥', isMinor: false, isMajor: true },
  { key: 'D', symbol: '♦', isMinor: true, isMajor: false },
  { key: 'C', symbol: '♣', isMinor: true, isMajor: false },
];

// Determine contract level based on tricks
function getContractLevel(tricks, strain) {
  if (typeof tricks !== 'number') return 'partscore';
  if (tricks >= 13) return 'grand';
  if (tricks >= 12) return 'slam';

  // Game thresholds vary by strain
  const isMinor = strain.key === 'C' || strain.key === 'D';
  const isMajor = strain.key === 'S' || strain.key === 'H';

  if (strain.key === 'NT' && tricks >= 9) return 'game';
  if (isMajor && tricks >= 10) return 'game';
  if (isMinor && tricks >= 11) return 'game';

  return 'partscore';
}

// Trick cell component
function TrickCell({ tricks, strain }) {
  const level = getContractLevel(tricks, strain);
  const displayValue = typeof tricks === 'number' ? tricks : '-';

  return (
    <td className={`trick-cell ${level}`}>
      <span className={`trick-value ${level}`}>
        {displayValue}
      </span>
    </td>
  );
}

// Legend component - subtle, right-aligned
function Legend() {
  return (
    <div className="trick-potential-legend">
      <div className="legend-item">
        <span className="legend-swatch game"></span>
        <span>Game</span>
      </div>
      <div className="legend-item">
        <span className="legend-swatch slam"></span>
        <span>Slam</span>
      </div>
      <div className="legend-item">
        <span className="legend-swatch grand"></span>
        <span>Grand</span>
      </div>
    </div>
  );
}

export function TrickPotentialChart({ ddTable, onClose, compact = false }) {
  if (!ddTable) return null;

  const suitColorClass = (symbol) =>
    symbol === '♥' || symbol === '♦' ? 'suit-red' : 'suit-black';

  const tableContent = (
    <div className="trick-potential-chart">
      <table>
        <thead>
          <tr>
            <th></th>
            {STRAINS.map(strain => (
              <th key={strain.key} className={suitColorClass(strain.symbol)}>
                {strain.symbol}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="row-label">NS</td>
            {STRAINS.map(strain => (
              <TrickCell
                key={strain.key}
                tricks={ddTable.NS?.[strain.key]}
                strain={strain}
              />
            ))}
          </tr>
          <tr>
            <td className="row-label">EW</td>
            {STRAINS.map(strain => (
              <TrickCell
                key={strain.key}
                tricks={ddTable.EW?.[strain.key]}
                strain={strain}
              />
            ))}
          </tr>
        </tbody>
      </table>
      <Legend />
    </div>
  );

  // Compact mode: just return the table inline
  if (compact) {
    return tableContent;
  }

  // Overlay mode: wrap in dismissible container
  return (
    <div className="trick-potential-overlay" onClick={onClose}>
      <div className="trick-potential-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-title">Possible Tricks</span>
            <ChartHelp chartType="possible-tricks" variant="icon" />
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        {tableContent}
        <div className="modal-footer">
          Perfect play analysis
        </div>
      </div>
    </div>
  );
}

/**
 * TrickPotentialButton - Small button to trigger the chart overlay
 */
export function TrickPotentialButton({ onClick, disabled = false }) {
  if (disabled) return null;

  return (
    <button
      onClick={onClick}
      className="trick-potential-button"
      title="View possible tricks"
      aria-label="View possible tricks table"
    >
      📊
    </button>
  );
}

export default TrickPotentialChart;
