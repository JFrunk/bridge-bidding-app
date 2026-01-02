import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * VerticalPlayableCard - Clickable card component optimized for vertical overlapping displays
 *
 * Designed specifically for East/West positions in the play phase.
 * Shows only the top ~20px when overlapped, with rank and suit clearly visible.
 *
 * Design Philosophy:
 * - Rank and suit ONLY in top-left corner - minimal display for vertical stacking
 * - Same dimensions as PlayableCard for consistency
 * - No center symbol or bottom content - clean appearance when overlapped
 *
 * @param {Object} props
 * @param {Object} props.card - Card object with rank and suit properties
 * @param {function} props.onClick - Click handler for playing the card
 * @param {boolean} props.disabled - If true, card is not clickable
 * @param {string} props.className - Additional Tailwind classes
 */
export function VerticalPlayableCard({ card, onClick, disabled = false, className }) {
  const suitColor = card.suit === '♥' || card.suit === '♦' ? 'text-suit-red' : 'text-suit-black';
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[card.rank] || card.rank;
  const isClickable = onClick && !disabled;

  const suitName = {
    '♠': 'Spades',
    '♥': 'Hearts',
    '♦': 'Diamonds',
    '♣': 'Clubs'
  }[card.suit] || card.suit;

  return (
    <div
      className={cn(
        "playable-card", // CRITICAL: This class enables overlap in CSS - size set by PlayComponents.css
        // Base styles - same as PlayableCard for consistent sizing
        "relative bg-white border border-gray-400 rounded-card shadow-md",
        "transition-all duration-200",
        isClickable && "cursor-pointer hover:-translate-y-4 hover:shadow-xl hover:z-50 clickable",
        disabled && "cursor-not-allowed",
        className
      )}
      onClick={!disabled ? onClick : undefined}
      onTouchEnd={(e) => {
        // CRITICAL: Always handle touch events to prevent stuck :active state
        e.preventDefault();
        if (!disabled && onClick) {
          onClick();
        }
      }}
      role={isClickable ? "button" : undefined}
      aria-label={`${displayRank} of ${suitName}`}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      } : undefined}
    >
      {/* Top-left corner ONLY - rank and suit side by side for compact vertical display */}
      <div className={cn(
        "absolute top-1 left-1.5 leading-none flex flex-row items-center gap-0.5",
        suitColor
      )}>
        <span className="text-lg font-bold">{displayRank}</span>
        <span className="text-base">{card.suit}</span>
      </div>

      {/* No center or bottom content - keeps card clean when heavily overlapped */}
    </div>
  );
}

VerticalPlayableCard.displayName = "VerticalPlayableCard";
