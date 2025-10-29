import { useState } from 'react';
import { Button } from "../ui/button";
import { cn } from "../../lib/utils";

/**
 * BiddingBox Component
 *
 * Interactive bidding interface for bridge game.
 * Follows SAYC bidding rules and validates legal bids.
 * Uses Shadcn Button component with Tailwind styling.
 *
 * @param {Object} props
 * @param {function} props.onBid - Callback when bid is made: (bid: string) => void
 * @param {boolean} props.disabled - If true, all buttons are disabled
 * @param {Array} props.auction - Current auction history for legal bid validation
 */
export function BiddingBox({ onBid, disabled, auction }) {
  const [level, setLevel] = useState(null);
  const suits = ['♣', '♦', '♥', '♠', 'NT'];
  const calls = ['Pass', 'X', 'XX'];

  // Find last real bid (not Pass/X/XX) to validate legal bids
  const lastRealBid = [...auction].reverse().find(b => !['Pass', 'X', 'XX'].includes(b.bid));
  const suitOrder = { '♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5 };

  /**
   * Check if a bid is legal according to bridge rules
   * Must be higher level OR same level with higher suit
   */
  const isBidLegal = (level, suit) => {
    if (!lastRealBid) return true;
    const lastLevel = parseInt(lastRealBid.bid[0], 10);
    const lastSuit = lastRealBid.bid.slice(1);
    if (level > lastLevel) return true;
    if (level === lastLevel && suitOrder[suit] > suitOrder[lastSuit]) return true;
    return false;
  };

  const handleBid = (suit) => {
    if (level) {
      onBid(suit === 'NT' ? `${level}NT` : `${level}${suit}`);
      setLevel(null);
    }
  };

  const handleCall = (call) => {
    onBid(call);
    setLevel(null);
  };

  return (
    <div className="flex flex-col gap-2.5 p-3 sm:p-4 bg-bg-secondary rounded-lg" data-testid="bidding-box">
      <h3 className="m-0 mb-2.5 text-white text-sm sm:text-base">Bidding</h3>

      {/* Level buttons (1-7) - Responsive sizing */}
      <div className="flex flex-row gap-1 sm:gap-2 justify-center" data-testid="bid-levels">
        {[1, 2, 3, 4, 5, 6, 7].map(l => (
          <Button
            key={l}
            onClick={() => setLevel(l)}
            variant={level === l ? "default" : "outline"}
            disabled={disabled}
            className="w-9 h-9 sm:w-12 sm:h-10 text-sm sm:text-base"
            aria-label={`Select level ${l}`}
            data-testid={`bid-level-${l}`}
          >
            {l}
          </Button>
        ))}
      </div>

      {/* Suit buttons - Responsive sizing */}
      <div className="flex flex-row gap-1 sm:gap-2 justify-center" data-testid="bid-suits">
        {suits.map(s => {
          const isLegal = !level || isBidLegal(level, s);
          return (
            <Button
              key={s}
              onClick={() => handleBid(s)}
              disabled={!level || disabled || !isLegal}
              variant="outline"
              className="w-9 h-9 sm:w-12 sm:h-10 text-sm sm:text-base"
              aria-label={`Bid ${level || ''} ${s === 'NT' ? 'No Trump' : s}`}
              data-testid={`bid-suit-${s === 'NT' ? 'NT' : s}`}
            >
              {s === 'NT' ? 'NT' : (
                <span className={cn(
                  s === '♥' || s === '♦' ? 'text-suit-red' : 'text-suit-black',
                  "text-base sm:text-lg"
                )}>
                  {s}
                </span>
              )}
            </Button>
          );
        })}
      </div>

      {/* Call buttons (Pass, X, XX) - Responsive sizing */}
      <div className="flex flex-row gap-1 sm:gap-2 justify-center" data-testid="bid-calls">
        {calls.map(c => (
          <Button
            key={c}
            onClick={() => handleCall(c)}
            disabled={disabled}
            variant="outline"
            className="w-12 h-9 sm:w-16 sm:h-10 text-sm sm:text-base"
            aria-label={c === 'X' ? 'Double' : c === 'XX' ? 'Redouble' : 'Pass'}
            data-testid={`bid-call-${c}`}
          >
            {c}
          </Button>
        ))}
      </div>
    </div>
  );
}

BiddingBox.displayName = "BiddingBox";
