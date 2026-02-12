import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * VerticalCard Component
 *
 * Optimized for vertical overlapping displays (East/West positions).
 * Designed to show only the top ~15-20px when overlapped, with rank and suit
 * clearly visible in the top-left corner.
 *
 * P0 FIX: Card sizing uses vmin units for proportional scaling at all zoom levels (80%-110%+)
 * - Card dimensions: clamp(50px, 7.5vmin, 80px) width × clamp(70px, 10.5vmin, 112px) height
 * - Ensures cards scale proportionally even when browser is zoomed to 100% or 110%
 *
 * Design Philosophy:
 * - Rank and suit in corners for visibility when overlapped
 * - Large, bold text for easy readability
 * - Large center suit symbol visible when card is hovered/selected
 *
 * @param {Object} props
 * @param {string} props.rank - Card rank: 'A', 'K', 'Q', 'J', 'T' (10), '9', etc.
 * @param {string} props.suit - Card suit: '♠', '♥', '♦', '♣'
 * @param {function} props.onClick - Optional click handler
 * @param {boolean} props.disabled - If true, card is not clickable
 * @param {string} props.className - Additional Tailwind classes
 * @param {Object} props.style - Inline styles (e.g., for margin/overlap)
 */
export function VerticalCard({ rank, suit, onClick, disabled = false, className, style }) {
  // Determine suit color (red for hearts/diamonds, black for spades/clubs)
  const suitColor = suit === '♥' || suit === '♦' ? 'text-suit-red' : 'text-suit-black';

  // Map 'T' to '10' for display
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[rank] || rank;

  // Determine if card is clickable
  const isClickable = onClick && !disabled;

  // P0 FIX: Use vmin units for proportional scaling at all zoom levels (80%-110%+)
  const cardStyle = {
    width: 'clamp(50px, 7.5vmin, 80px)',
    height: 'clamp(70px, 10.5vmin, 112px)',
    ...style
  };

  return (
    <div
      className={cn(
        // Base styles - using inline style for vmin-based sizing
        "relative bg-white rounded-card",
        "border border-gray-400", // Full border like BridgeCard
        "shadow-md", // Same shadow as BridgeCard
        // Rotate each card 90 degrees counter-clockwise for vertical display
        "-rotate-90",
        // Hover effect (only if clickable) - lift card up to show it fully
        "transition-transform duration-200",
        isClickable && "cursor-pointer hover:-translate-y-4 hover:z-50 hover:shadow-md",
        // Disabled state
        disabled && "cursor-not-allowed",
        // Allow custom classes
        className
      )}
      style={cardStyle}
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
      {/* Top-left corner - ONLY visible indicator when overlapped
          Rank on left, suit on right - horizontally aligned */}
      <div className={cn(
        "absolute top-1 left-1.5 leading-none flex flex-row items-start gap-0.5",
        suitColor
      )}>
        <span className="text-lg font-bold leading-none">{displayRank}</span>
        <span className="text-base leading-none mt-0.5">{suit}</span>
      </div>

      {/* Bottom-right corner - mirror of top-left, rotated 180° */}
      <div className={cn(
        "absolute bottom-1 right-1.5 leading-none flex flex-row items-start gap-0.5 rotate-180",
        suitColor
      )}>
        <span className="text-lg font-bold leading-none">{displayRank}</span>
        <span className="text-base leading-none mt-0.5">{suit}</span>
      </div>

      {/* Center suit symbol - large and prominent, visible when card is hovered/selected */}
      <div className={cn("absolute inset-0 flex items-center justify-center", suitColor)}>
        <span className="text-5xl">{suit}</span>
      </div>
    </div>
  );
}

VerticalCard.displayName = "VerticalCard";
