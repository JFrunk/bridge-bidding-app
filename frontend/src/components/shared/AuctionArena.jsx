/**
 * AuctionArena - Bidding History Grid Component
 *
 * Displays the auction in a 4-column grid (West | North | East | South)
 * that fits into the center slot of ReactorLayout.
 *
 * Similar to TrickArena but for bidding sequences instead of played cards.
 *
 * Props:
 * - auctionHistory: Array of bids [{bid, position?}, ...] or strings
 * - dealer: Starting dealer position ('N', 'E', 'S', 'W')
 * - currentPosition: Number of bids to show (for replay stepping)
 * - userPosition: User's seat for highlighting ('S' by default)
 * - scaleClass: Tailwind text scale class
 */

import React, { useMemo } from 'react';
import { BidChip } from './BidChip';

const POSITIONS = ['W', 'N', 'E', 'S']; // Display order for auction grid

// Normalize position from full name to single letter
const normalizePosition = (pos) => {
  if (!pos) return 'N';
  const posMap = { 'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W' };
  return posMap[pos] || pos;
};

const AuctionArena = ({
  auctionHistory = [],
  dealer = 'N',
  currentPosition = 0,
  userPosition = 'S',
  scaleClass = 'text-base',
}) => {
  const normalizedDealer = normalizePosition(dealer);
  const dealerIndex = POSITIONS.indexOf(normalizedDealer);

  // Build rows of bids for display
  const rows = useMemo(() => {
    if (!auctionHistory || auctionHistory.length === 0 || currentPosition === 0) {
      return [];
    }

    const visibleBids = auctionHistory.slice(0, currentPosition);
    const result = [];
    let currentRow = new Array(4).fill(null);

    // Fill empty cells before dealer
    for (let i = 0; i < dealerIndex; i++) {
      currentRow[i] = { empty: true };
    }

    let colIndex = dealerIndex;

    visibleBids.forEach((bidInfo) => {
      const bid = typeof bidInfo === 'string' ? bidInfo : bidInfo.bid;
      const position = POSITIONS[colIndex];
      const isUserBid = position === userPosition;

      currentRow[colIndex] = {
        bid,
        position,
        isUserBid,
      };

      colIndex++;
      if (colIndex >= 4) {
        result.push([...currentRow]);
        currentRow = new Array(4).fill(null);
        colIndex = 0;
      }
    });

    // Push final partial row if it has content
    if (currentRow.some((c) => c !== null)) {
      result.push(currentRow);
    }

    return result;
  }, [auctionHistory, dealerIndex, currentPosition, userPosition]);

  // Start state - no bids yet
  if (currentPosition === 0) {
    return (
      <div className={`${scaleClass} auction-arena auction-arena-start`}>
        <div className="flex flex-col items-center justify-center gap-2 p-6 bg-black/20 rounded-lg border border-white/10 min-w-[14em] min-h-[10em]">
          <div className="text-white font-bold text-[1.2em]">Bidding Review</div>
          <div className="text-white/70 text-[0.85em]">Dealer: {dealer}</div>
          <div className="text-white/50 text-[0.75em]">Step through to see each bid</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${scaleClass} auction-arena`}>
      <div className="bg-black/20 rounded-lg border border-white/10 p-3 min-w-[16em]">
        {/* Header row with position labels */}
        <div className="grid grid-cols-4 gap-1 mb-2">
          {POSITIONS.map((pos) => (
            <div
              key={pos}
              className={`text-center text-[0.7em] font-semibold uppercase tracking-wider
                ${pos === userPosition ? 'text-blue-300' : 'text-white/60'}`}
            >
              {pos}
              {pos === normalizedDealer && (
                <span className="ml-1 text-yellow-400">(D)</span>
              )}
            </div>
          ))}
        </div>

        {/* Bid rows */}
        <div className="flex flex-col gap-1">
          {rows.map((row, rowIdx) => (
            <div key={rowIdx} className="grid grid-cols-4 gap-1">
              {row.map((cell, colIdx) => (
                <div
                  key={colIdx}
                  className={`flex items-center justify-center min-h-[2em] rounded
                    ${cell?.isUserBid ? 'bg-blue-500/20' : ''}
                    ${cell?.empty ? 'bg-transparent' : ''}`}
                >
                  {cell?.bid && <BidChip bid={cell.bid} size="sm" />}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AuctionArena;
