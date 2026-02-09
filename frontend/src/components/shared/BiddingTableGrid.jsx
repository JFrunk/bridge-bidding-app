import * as React from "react";
import { BidChip } from "./BidChip";

/**
 * BiddingTableGrid - Shared bidding history table component
 *
 * REUSABLE across:
 * - Main bidding phase (App.js BiddingTable)
 * - Play phase bid history popup (ContractHeader)
 *
 * Displays a 4-column grid (N-E-S-W) with dealer-based row wrapping.
 * Blank cells appear before the dealer's position on row 0.
 *
 * Per UI_UX_CONSTITUTION.md - uses BidChip for high-contrast white pills.
 */
export function BiddingTableGrid({
  auction = [],
  dealer = 'North',
  players = ['North', 'East', 'South', 'West'],
  nextPlayerIndex = 0,
  onBidClick,
  isComplete = false,
  compact = false,  // Compact mode for popups
  showDealerIndicator = true
}) {
  // Map dealer to index
  const dealerFull = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' }[dealer] || dealer;
  const dealerShort = { 'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W' }[dealerFull] || 'N';
  const dealerIndex = players.indexOf(dealerFull);

  // Build a 2D grid: rows[rowIndex][columnIndex] = bid object or null
  const grid = [];
  let currentRow = 0;
  let currentCol = dealerIndex >= 0 ? dealerIndex : 0; // Start at dealer's column

  for (let i = 0; i < auction.length; i++) {
    const bid = auction[i];

    // Ensure row exists with 4 null cells
    if (!grid[currentRow]) {
      grid[currentRow] = [null, null, null, null]; // [North, East, South, West]
    }

    // Place bid in current position
    grid[currentRow][currentCol] = bid;

    // Move to next column (wrapping around)
    currentCol = (currentCol + 1) % 4;

    // If we just wrapped to North column (column 0), move to next row
    if (currentCol === 0 && i < auction.length - 1) {
      currentRow++;
    }
  }

  // If auction is empty, ensure we show at least one empty row
  if (grid.length === 0) {
    grid.push([null, null, null, null]);
  }

  // Helper to show dealer indicator
  const dealerIndicator = (pos) => {
    if (!showDealerIndicator) return '';
    const posShort = { 'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W' }[pos] || pos;
    return dealerShort === posShort ? ' (D)' : '';
  };

  // Helper to get header highlight class (for active bidding)
  const getHeaderClass = (position) => {
    if (isComplete) return '';
    return players[nextPlayerIndex] === position ? 'current-player' : '';
  };

  // Helper to get cell highlight class
  const getCellHighlightClass = (rowIndex, colIndex, row) => {
    if (isComplete) return '';
    const isActiveRow = rowIndex === grid.length - 1;
    if (!isActiveRow) return '';
    const cellPlayer = players[colIndex];
    if (cellPlayer === players[nextPlayerIndex] && row[colIndex] === null) {
      return 'current-player';
    }
    return '';
  };

  // Format bid for display - handles both string and object formats
  // Returns a BidChip component for high-contrast display per UI_UX_CONSTITUTION.md
  const formatBid = (bid, onClick) => {
    if (!bid) return null;
    const bidStr = typeof bid === 'string' ? bid : (bid.bid || '');
    if (!bidStr) return null;
    return <BidChip bid={bidStr} onClick={onClick ? () => onClick(bid) : undefined} />;
  };

  // Compact mode uses simpler styling for popups
  if (compact) {
    return (
      <table className="bid-history-table">
        <thead>
          <tr>
            <th>N{dealerIndicator('North')}</th>
            <th>E{dealerIndicator('East')}</th>
            <th>S{dealerIndicator('South')}</th>
            <th>W{dealerIndicator('West')}</th>
          </tr>
        </thead>
        <tbody>
          {grid.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {[0, 1, 2, 3].map(col => (
                <td key={col}>{formatBid(row[col], onBidClick)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  // Full mode with highlighting and click handlers
  return (
    <table className="bidding-table" data-testid="bidding-table">
      <thead>
        <tr>
          <th className={getHeaderClass('North')} data-testid="bidding-header-north">
            North{dealerIndicator('North')}
          </th>
          <th className={getHeaderClass('East')} data-testid="bidding-header-east">
            East{dealerIndicator('East')}
          </th>
          <th className={getHeaderClass('South')} data-testid="bidding-header-south">
            South{dealerIndicator('South')}
          </th>
          <th className={getHeaderClass('West')} data-testid="bidding-header-west">
            West{dealerIndicator('West')}
          </th>
        </tr>
      </thead>
      <tbody data-testid="bidding-table-body">
        {grid.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {[0, 1, 2, 3].map(colIndex => (
              <td
                key={colIndex}
                className={getCellHighlightClass(rowIndex, colIndex, row)}
              >
                {formatBid(row[colIndex], onBidClick)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
