import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * PlayableCard - Clickable card component for the play phase
 * Similar to BridgeCard but optimized for play interactions
 * Follows "Rule of Three" and senior-friendly UX principles
 *
 * @param {boolean} compact - If true, shows rank and suit side-by-side (for vertical overlapping displays)
 */
export function PlayableCard({ card, onClick, disabled = false, compact = false, className }) {
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
        "playable-card", // CRITICAL: This class enables -45px overlap in CSS
        "relative w-[70px] h-[100px] bg-white border border-gray-400 rounded-card shadow-md",
        "transition-all duration-200",
        isClickable && "cursor-pointer hover:-translate-y-4 hover:shadow-xl hover:z-50 clickable",
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
      {/* Top-left corner - compact mode shows rank+suit horizontally */}
      <div className={cn(
        "absolute top-1 left-1.5 leading-none",
        compact ? "flex flex-row items-center gap-0.5" : "flex flex-col items-center",
        suitColor
      )}>
        <span className={cn("font-bold", compact ? "text-xl" : "text-lg")}>{displayRank}</span>
        <span className={cn(compact ? "text-xl" : "text-base")}>{card.suit}</span>
      </div>

      {/* Center suit symbol - hidden in compact mode (saves space for overlapping) */}
      {!compact && (
        <div className={cn("absolute inset-0 flex items-center justify-center", suitColor)}>
          <span className="text-4xl">{card.suit}</span>
        </div>
      )}

      {/* Bottom-right corner (rotated) - hidden in compact mode */}
      {!compact && (
        <div className={cn("absolute bottom-1 right-1.5 flex flex-col items-center rotate-180 leading-none", suitColor)}>
          <span className="text-lg font-bold">{displayRank}</span>
          <span className="text-base">{card.suit}</span>
        </div>
      )}
    </div>
  );
}
