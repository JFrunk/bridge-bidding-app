import React from 'react';
import PropTypes from 'prop-types';
import { formatBid } from '../types/flow-types';
import './BidTable.css';

/**
 * Seat order for the table columns (always N, E, S, W)
 */
const SEAT_ORDER = ['N', 'E', 'S', 'W'];

/**
 * Get the index of a seat in the column order
 * @param {string} seat - 'N', 'E', 'S', or 'W'
 * @returns {number} Column index (0-3)
 */
const getSeatIndex = (seat) => SEAT_ORDER.indexOf(seat);

/**
 * Render a bid with colorized suit symbols
 * @param {string} bid - The bid string (e.g., "1H", "3NT", "Pass")
 * @param {boolean} isActive - Whether this bid should be highlighted
 * @returns {React.ReactNode}
 */
const renderBid = (bid, isActive = false) => {
  if (!bid) {
    return <span className="empty-cell">&mdash;</span>;
  }

  const formattedBid = formatBid(bid);

  if (formattedBid === 'Pass') {
    return <span className={`pass ${isActive ? 'bid-active' : ''}`}>Pass</span>;
  }

  if (formattedBid === 'X' || formattedBid === 'XX') {
    return <span className={isActive ? 'bid-active' : ''}>{formattedBid}</span>;
  }

  // Check for suit symbols and colorize them
  const suitMatch = formattedBid.match(/^(\d)([\u2660\u2665\u2666\u2663]|NT)$/);
  if (suitMatch) {
    const [, level, strain] = suitMatch;

    if (strain === 'NT') {
      return <span className={isActive ? 'bid-active' : ''}>{level}NT</span>;
    }

    // Determine color: hearts and diamonds are red, spades and clubs are black
    const isRed = strain === '\u2665' || strain === '\u2666'; // hearts or diamonds

    return (
      <span className={isActive ? 'bid-active' : ''}>
        {level}
        <span className={`bid-suit ${isRed ? 'red' : 'black'}`}>{strain}</span>
      </span>
    );
  }

  // Fallback for any other format
  return <span className={isActive ? 'bid-active' : ''}>{formattedBid}</span>;
};

/**
 * BidTable - Displays auction history in a 4-column table format
 *
 * @param {Object} props
 * @param {Array<{bid: string, bidder: string, explanation?: string}>} props.bids - Array of bids
 * @param {string} props.dealer - Who dealt ('N', 'E', 'S', or 'W')
 * @param {string} props.playerSeat - Player's seat to highlight (default: 'S')
 * @param {number} props.activeBidIndex - Optional index of bid to highlight
 */
const BidTable = ({
  bids = [],
  dealer = 'N',
  playerSeat = 'S',
  activeBidIndex
}) => {
  // Calculate which column the dealer is in
  const dealerColIndex = getSeatIndex(dealer);
  const playerColIndex = getSeatIndex(playerSeat);

  // Organize bids into rows
  // Each row has 4 cells (N, E, S, W)
  // First row starts with empty cells before the dealer
  const rows = [];
  let currentRow = new Array(4).fill(null);
  let colIndex = dealerColIndex;
  let bidIndex = 0;

  // Fill in empty cells before dealer in first row
  for (let i = 0; i < dealerColIndex; i++) {
    currentRow[i] = { isEmpty: true };
  }

  // Place each bid in the correct position
  for (const bid of bids) {
    currentRow[colIndex] = {
      ...bid,
      originalIndex: bidIndex
    };

    colIndex++;
    bidIndex++;

    // Move to next row if we've filled all 4 columns
    if (colIndex >= 4) {
      rows.push(currentRow);
      currentRow = new Array(4).fill(null);
      colIndex = 0;
    }
  }

  // Add the last row if it has any bids
  if (currentRow.some(cell => cell !== null)) {
    rows.push(currentRow);
  }

  // If no bids yet, still show the header row
  if (rows.length === 0 && dealerColIndex > 0) {
    // Show first row with empty cells before dealer
    const emptyRow = new Array(4).fill(null);
    for (let i = 0; i < dealerColIndex; i++) {
      emptyRow[i] = { isEmpty: true };
    }
    rows.push(emptyRow);
  }

  return (
    <table className="bid-table">
      <thead>
        <tr>
          {SEAT_ORDER.map((seat, idx) => (
            <th
              key={seat}
              className={idx === playerColIndex ? 'you' : ''}
            >
              {seat}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {row.map((cell, cellIndex) => {
              const isPlayerCol = cellIndex === playerColIndex;
              const isActive = cell && !cell.isEmpty && cell.originalIndex === activeBidIndex;

              return (
                <td
                  key={cellIndex}
                  className={isPlayerCol ? 'you-col' : ''}
                  title={cell?.explanation || undefined}
                >
                  {cell?.isEmpty
                    ? <span className="empty-cell">&mdash;</span>
                    : renderBid(cell?.bid, isActive)
                  }
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

BidTable.propTypes = {
  bids: PropTypes.arrayOf(
    PropTypes.shape({
      bid: PropTypes.string.isRequired,
      bidder: PropTypes.oneOf(['N', 'E', 'S', 'W']).isRequired,
      explanation: PropTypes.string,
    })
  ),
  dealer: PropTypes.oneOf(['N', 'E', 'S', 'W']),
  playerSeat: PropTypes.oneOf(['N', 'E', 'S', 'W']),
  activeBidIndex: PropTypes.number,
};

export default BidTable;
