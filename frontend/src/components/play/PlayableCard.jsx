import * as React from "react";
import { cn } from "../../lib/utils";
import { getSuitColorClass, SUIT_NAMES } from "../../utils/suitColors";
import { rankToDisplay } from "../../shared/utils/cardUtils";

/**
 * PlayableCard - Clickable card component for the play phase
 * Similar to BridgeCard but optimized for play interactions
 * Follows "Rule of Three" and senior-friendly UX principles
 *
 * @param {boolean} compact - If true, shows rank and suit side-by-side (for vertical overlapping displays)
 * @param {boolean} readOnly - If true, removes all interactive affordances (for review/display modes)
 */
export function PlayableCard({ card, onClick, disabled = false, compact = false, readOnly = false, className }) {
  const suitColor = getSuitColorClass(card.suit);
  const displayRank = rankToDisplay(card.rank);
  const isClickable = onClick && !disabled && !readOnly;

  const suitName = SUIT_NAMES[card.suit] || card.suit;

  return (
    <div
      className={cn(
        "playable-card", // CRITICAL: This class enables overlap and responsive sizing in CSS
        "relative bg-white border-[1px] border-gray-300 rounded-card shadow-[1px_1px_3px_rgba(0,0,0,0.3)]",
        !readOnly && "transition-all duration-200",
        isClickable && "cursor-pointer hover:-translate-y-4 hover:shadow-xl hover:z-50 clickable",
        disabled && !readOnly && "cursor-not-allowed",
        readOnly && "read-only cursor-default",
        className
      )}
      onClick={!disabled ? onClick : undefined}
      onTouchEnd={(e) => {
        // CRITICAL: Always handle touch events to prevent stuck :active state
        // Even on disabled cards, we need to complete the touch event
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
      {/* Top-left corner - compact mode shows rank+suit horizontally */}
      <div className={cn(
        "absolute top-1 left-1.5 leading-none",
        compact ? "flex flex-row items-center gap-0.5" : "flex flex-col items-center",
        suitColor
      )}>
        <span className={cn("font-bold", compact ? "text-xl" : "text-lg")}>{displayRank}</span>
        <span className={cn(compact ? "text-xl" : "text-base")}>{card.suit}</span>
      </div>

      {/* Center and bottom-right removed for compact mobile-friendly display */}
    </div>
  );
}
