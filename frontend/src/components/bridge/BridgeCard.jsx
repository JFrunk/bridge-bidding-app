import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * BridgeCard Component
 *
 * Displays a playing card with rank and suit in standard bridge card styling.
 * Uses Tailwind CSS for styling following the Rule of Three design system.
 *
 * @param {Object} props
 * @param {string} props.rank - Card rank: 'A', 'K', 'Q', 'J', 'T' (10), '9', etc.
 * @param {string} props.suit - Card suit: '♠', '♥', '♦', '♣'
 * @param {function} props.onClick - Optional click handler
 * @param {boolean} props.disabled - If true, card is not clickable
 * @param {string} props.className - Additional Tailwind classes
 */
export function BridgeCard({ rank, suit, onClick, disabled = false, className }) {
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
        // Base styles - Rule of Three: spacing (gap-4), border-radius (rounded-card)
        "relative w-[70px] h-[100px] bg-white border border-gray-400 rounded-card shadow-md",
        // Hover effect (only if clickable)
        "transition-transform duration-200",
        isClickable && "cursor-pointer hover:-translate-y-4 hover:z-50",
        // Disabled state
        disabled && "opacity-60 cursor-not-allowed",
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
      {/* Top-left corner */}
      <div className={cn("absolute top-1 left-1.5 flex flex-col items-center leading-none", suitColor)}>
        <span className="text-lg font-bold">{displayRank}</span>
        <span className="text-base">{suit}</span>
      </div>

      {/* Center suit symbol */}
      <div className={cn("absolute inset-0 flex items-center justify-center", suitColor)}>
        <span className="text-4xl">{suit}</span>
      </div>

      {/* Bottom-right corner (rotated) */}
      <div className={cn("absolute bottom-1 right-1.5 flex flex-col items-center rotate-180 leading-none", suitColor)}>
        <span className="text-lg font-bold">{displayRank}</span>
        <span className="text-base">{suit}</span>
      </div>
    </div>
  );
}

BridgeCard.displayName = "BridgeCard";
