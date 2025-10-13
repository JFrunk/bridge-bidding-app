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
    <div className="flex flex-col gap-2.5 p-4 bg-bg-secondary rounded-lg">
      <h3 className="m-0 mb-2.5 text-white text-base">Bidding</h3>

      {/* Level buttons (1-7) */}
      <div className="flex flex-row gap-2 justify-center">
        {[1, 2, 3, 4, 5, 6, 7].map(l => (
          <Button
            key={l}
            onClick={() => setLevel(l)}
            variant={level === l ? "default" : "outline"}
            disabled={disabled}
            className="w-12 h-10"
            aria-label={`Select level ${l}`}
          >
            {l}
          </Button>
        ))}
      </div>

      {/* Suit buttons */}
      <div className="flex flex-row gap-2 justify-center">
        {suits.map(s => {
          const isLegal = !level || isBidLegal(level, s);
          return (
            <Button
              key={s}
              onClick={() => handleBid(s)}
              disabled={!level || disabled || !isLegal}
              variant="outline"
              className="w-12 h-10"
              aria-label={`Bid ${level || ''} ${s === 'NT' ? 'No Trump' : s}`}
            >
              {s === 'NT' ? 'NT' : (
                <span className={cn(
                  s === '♥' || s === '♦' ? 'text-suit-red' : 'text-suit-black',
                  "text-lg"
                )}>
                  {s}
                </span>
              )}
            </Button>
          );
        })}
      </div>

      {/* Call buttons (Pass, X, XX) */}
      <div className="flex flex-row gap-2 justify-center">
        {calls.map(c => (
          <Button
            key={c}
            onClick={() => handleCall(c)}
            disabled={disabled}
            variant="outline"
            className="w-16 h-10"
            aria-label={c === 'X' ? 'Double' : c === 'XX' ? 'Redouble' : 'Pass'}
          >
            {c}
          </Button>
        ))}
      </div>
    </div>
  );
}

BiddingBox.displayName = "BiddingBox";
