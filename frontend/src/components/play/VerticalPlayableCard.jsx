import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * VerticalPlayableCard - Clickable card component optimized for vertical overlapping displays
 *
 * Designed specifically for East/West positions in the play phase.
 * Shows only the top ~15-20px when overlapped, with rank and suit clearly visible.
 *
 * Design Philosophy:
 * - Rank and suit ONLY in top-left corner (no bottom-right)
 * - Large, bold text for easy readability when heavily overlapped (80-85% overlap)
 * - Large center suit symbol visible when card is hovered/selected
 * - Similar to classic playing card design
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
        "playable-card", // CRITICAL: This class enables overlap in CSS
        // Base styles - minimal border/shadow for smooth vertical stacking
        "relative w-[70px] h-[100px] bg-white rounded-card",
        "border-t border-l border-r border-gray-400", // Top, left, right borders only
        "shadow-sm", // Lighter shadow
        "transition-all duration-200",
        isClickable && "cursor-pointer hover:-translate-y-4 hover:shadow-xl hover:z-50 hover:border clickable",
        disabled && "cursor-not-allowed",
        className
      )}
      onClick={!disabled ? onClick : undefined}
      onTouchEnd={!disabled ? (e) => {
        // Prevent ghost clicks on mobile
        e.preventDefault();
        onClick?.();
      } : undefined}
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
      {/* Top-left corner - ONLY visible indicator when overlapped
          Rank on left, suit on right - horizontally aligned */}
      <div className={cn(
        "absolute top-0.5 left-1 leading-none flex flex-row items-start gap-0.5",
        suitColor
      )}>
        <span className="text-2xl font-bold leading-none">{displayRank}</span>
        <span className="text-lg leading-none mt-0.5">{card.suit}</span>
      </div>

      {/* Bottom-right corner - mirror of top-left, rotated 180° */}
      <div className={cn(
        "absolute bottom-0.5 right-1 leading-none flex flex-row items-start gap-0.5 rotate-180",
        suitColor
      )}>
        <span className="text-2xl font-bold leading-none">{displayRank}</span>
        <span className="text-lg leading-none mt-0.5">{card.suit}</span>
      </div>

      {/* Center suit symbol - large and prominent, visible when card is hovered/selected */}
      <div className={cn("absolute inset-0 flex items-center justify-center", suitColor)}>
        <span className="text-5xl">{card.suit}</span>
      </div>
    </div>
  );
}

VerticalPlayableCard.displayName = "VerticalPlayableCard";
