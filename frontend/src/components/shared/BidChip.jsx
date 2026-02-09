/**
 * BidChip Component
 * Per UI_UX_CONSTITUTION.md - "The Bid Chip Rule":
 * Wrap every bid in a white rounded pill (bg-white rounded px-2 py-0.5 shadow-sm)
 * to ensure Red/Black suit colors are legible on dark green surfaces.
 *
 * Color Logic:
 * - Hearts (♥) and Diamonds (♦) = text-red-600
 * - Spades (♠), Clubs (♣), and NT = text-gray-900
 * - Special bids (Pass, X, XX) = text-gray-500
 */

import React from 'react';
import { getSuitColorClass, extractSuitFromBid, isSpecialBid, formatBidDisplay } from '../../utils/suitColors';

/**
 * BidChip - White pill containing a bid with proper suit coloring
 * @param {Object} props
 * @param {string} props.bid - The bid string (e.g., "1S", "2♥", "Pass", "X")
 * @param {string} [props.className] - Additional CSS classes
 * @param {function} [props.onClick] - Click handler
 */
export function BidChip({ bid, className = '', onClick }) {
  if (!bid) return null;

  // Format bid for display (convert S->♠, etc.)
  const displayBid = formatBidDisplay(typeof bid === 'object' ? bid.bid : bid);

  // Determine suit and color class
  const suit = extractSuitFromBid(displayBid);
  const isSpecial = isSpecialBid(displayBid);

  // Get color class - special bids are muted gray
  const colorClass = isSpecial ? 'text-gray-500' : getSuitColorClass(suit, false);

  return (
    <span
      className={`inline-flex items-center justify-center bg-white rounded-md px-2 py-0.5 shadow-sm border border-gray-200 ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <span className={`font-bold text-sm ${colorClass}`}>
        {displayBid}
      </span>
    </span>
  );
}

export default BidChip;
