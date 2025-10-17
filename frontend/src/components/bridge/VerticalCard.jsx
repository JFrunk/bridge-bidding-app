import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * VerticalCard Component
 *
 * Optimized for vertical overlapping displays (East/West positions).
 * Designed to show only the top ~15-20px when overlapped, with rank and suit
 * clearly visible in the top-left corner.
 *
 * Design Philosophy:
 * - Rank and suit ONLY in top-left corner (no bottom-right corner)
 * - Large, bold text for easy readability when heavily overlapped
 * - Large center suit symbol visible when card is hovered/selected
 * - Minimal design similar to classic playing cards
 *
 * @param {Object} props
 * @param {string} props.rank - Card rank: 'A', 'K', 'Q', 'J', 'T' (10), '9', etc.
 * @param {string} props.suit - Card suit: '♠', '♥', '♦', '♣'
 * @param {function} props.onClick - Optional click handler
 * @param {boolean} props.disabled - If true, card is not clickable
 * @param {string} props.className - Additional Tailwind classes
 */
export function VerticalCard({ rank, suit, onClick, disabled = false, className }) {
  // Determine suit color (red for hearts/diamonds, black for spades/clubs)
  const suitColor = suit === '♥' || suit === '♦' ? 'text-suit-red' : 'text-suit-black';

  // Map 'T' to '10' for display
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[rank] || rank;

  // Determine if card is clickable
  const isClickable = onClick && !disabled;

  return (
    <div
      className={cn(
        // Base styles - minimal border/shadow for smooth vertical stacking
        "relative w-[70px] h-[100px] bg-white rounded-card",
        "border-t border-l border-r border-gray-400", // Top, left, right borders only
        "shadow-sm", // Lighter shadow
        // Hover effect (only if clickable) - lift card up to show it fully
        "transition-transform duration-200",
        isClickable && "cursor-pointer hover:-translate-y-4 hover:z-50 hover:shadow-md hover:border",
        // Disabled state
        disabled && "cursor-not-allowed",
        // Allow custom classes
        className
      )}
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
        "absolute top-0.5 left-1 leading-none flex flex-row items-start gap-0.5",
        suitColor
      )}>
        <span className="text-2xl font-bold leading-none">{displayRank}</span>
        <span className="text-lg leading-none mt-0.5">{suit}</span>
      </div>

      {/* Bottom-right corner - mirror of top-left, rotated 180° */}
      <div className={cn(
        "absolute bottom-0.5 right-1 leading-none flex flex-row items-start gap-0.5 rotate-180",
        suitColor
      )}>
        <span className="text-2xl font-bold leading-none">{displayRank}</span>
        <span className="text-lg leading-none mt-0.5">{suit}</span>
      </div>

      {/* Center suit symbol - large and prominent, visible when card is hovered/selected */}
      <div className={cn("absolute inset-0 flex items-center justify-center", suitColor)}>
        <span className="text-5xl">{suit}</span>
      </div>
    </div>
  );
}

VerticalCard.displayName = "VerticalCard";
