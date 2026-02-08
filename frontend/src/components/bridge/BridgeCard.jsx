import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * BridgeCard Component
 *
 * Displays a playing card with rank and suit in standard bridge card styling.
 * Content is positioned in the LEFT visible strip to remain visible when cards overlap.
 *
 * Per CC_CORRECTIONS:
 * - Card width: 48px, overlap: -16px, visible strip: 32px
 * - Content positioned in left 32px strip (or full width for last card)
 *
 * @param {Object} props
 * @param {string} props.rank - Card rank: 'A', 'K', 'Q', 'J', 'T' (10), '9', etc.
 * @param {string} props.suit - Card suit: '♠', '♥', '♦', '♣'
 * @param {function} props.onClick - Optional click handler
 * @param {boolean} props.disabled - If true, card is not clickable
 * @param {string} props.className - Additional classes
 */
export function BridgeCard({ rank, suit, onClick, disabled = false, className }) {
  // Determine suit color
  const isRed = suit === '♥' || suit === '♦';
  const colorClass = isRed ? 'red' : 'black';

  // Map 'T' to '10' for display
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[rank] || rank;

  // Determine if card is clickable
  const isClickable = onClick && !disabled;

  return (
    <div
      className={cn("card", colorClass, isClickable && "clickable", className)}
      onClick={!disabled ? onClick : undefined}
      role={isClickable ? "button" : undefined}
      aria-label={`${displayRank} of ${suit === '♠' ? 'Spades' : suit === '♥' ? 'Hearts' : suit === '♦' ? 'Diamonds' : 'Clubs'}`}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      } : undefined}
    >
      {/* Content positioned in left visible strip */}
      <div className="card-content">
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol">{suit}</span>
      </div>
    </div>
  );
}

BridgeCard.displayName = "BridgeCard";
