import * as React from "react";
import { cn } from "../../lib/utils";

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

// Get border class for contract level
function getBorderClass(level) {
  switch (level) {
    case 'grand':
      return 'ring-2 ring-red-500';
    case 'slam':
      return 'ring-2 ring-orange-400';
    case 'game':
      return 'ring-2 ring-green-500';
    default:
      return '';
  }
}

// Trick cell component
function TrickCell({ tricks, strain }) {
  const level = getContractLevel(tricks, strain);
  const borderClass = getBorderClass(level);

  return (
    <td className="px-2 py-1 text-center">
      <span
        className={cn(
          "inline-block w-7 h-7 leading-7 rounded text-sm font-medium",
          borderClass,
          level === 'partscore' && "text-gray-300"
        )}
      >
        {tricks}
      </span>
    </td>
  );
}

// Legend component
function Legend() {
  return (
    <div className="flex items-center gap-3 text-xs text-gray-400 mt-2">
      <div className="flex items-center gap-1">
        <span className="inline-block w-3 h-3 rounded ring-2 ring-green-500"></span>
        <span>Game</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="inline-block w-3 h-3 rounded ring-2 ring-orange-400"></span>
        <span>Slam</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="inline-block w-3 h-3 rounded ring-2 ring-red-500"></span>
        <span>Grand</span>
      </div>
    </div>
  );
}

export function TrickPotentialChart({ ddTable, onClose, compact = false }) {
  if (!ddTable) return null;

  const suitColor = (symbol) =>
    symbol === '♥' || symbol === '♦' ? 'text-suit-red' : 'text-suit-black';

  const tableContent = (
    <div className="trick-potential-chart">
      <table className="w-full text-center">
        <thead>
          <tr className="text-gray-400 text-sm">
            <th className="px-2 py-1"></th>
            {STRAINS.map(strain => (
              <th key={strain.key} className={cn("px-2 py-1", suitColor(strain.symbol))}>
                {strain.symbol}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="text-white">
          <tr>
            <td className="px-2 py-1 text-left text-gray-300 font-medium">NS</td>
            {STRAINS.map(strain => (
              <TrickCell
                key={strain.key}
                tricks={ddTable.NS?.[strain.key] ?? '-'}
                strain={strain}
              />
            ))}
          </tr>
          <tr>
            <td className="px-2 py-1 text-left text-gray-300 font-medium">EW</td>
            {STRAINS.map(strain => (
              <TrickCell
                key={strain.key}
                tricks={ddTable.EW?.[strain.key] ?? '-'}
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-bg-secondary rounded-lg shadow-xl p-4 max-w-xs"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-200">Trick Potential</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-lg leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        {tableContent}
        <p className="text-xs text-gray-500 mt-3 text-center">
          Double-dummy analysis
        </p>
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
      className={cn(
        "inline-flex items-center justify-center",
        "w-7 h-7 rounded",
        "bg-bg-tertiary hover:bg-bg-secondary",
        "text-gray-400 hover:text-white",
        "transition-colors duration-150",
        "text-sm"
      )}
      title="View trick potential"
      aria-label="View trick potential chart"
    >
      📊
    </button>
  );
}

export default TrickPotentialChart;
