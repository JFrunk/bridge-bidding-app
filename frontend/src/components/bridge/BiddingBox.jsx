import { useState } from 'react';
import './BiddingBox.css';

/**
 * BiddingBox Component
 *
 * Interactive bidding interface for bridge game.
 * Follows SAYC bidding rules and validates legal bids.
 * Uses cream buttons with colored suit symbols per UI redesign spec.
 *
 * @param {Object} props
 * @param {function} props.onBid - Callback when bid is made: (bid: string) => void
 * @param {boolean} props.disabled - If true, all buttons are disabled
 * @param {Array} props.auction - Current auction history for legal bid validation
 */
export function BiddingBox({ onBid, disabled, auction }) {
  const [level, setLevel] = useState(null);
  const suits = ['♣', '♦', '♥', '♠', 'NT'];
  const levels = [1, 2, 3, 4, 5, 6, 7];

  // Find last real bid (not Pass/X/XX) to validate legal bids
  const lastRealBid = [...auction].reverse().find(b => !['Pass', 'X', 'XX'].includes(b.bid));
  const suitOrder = { '♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5 };

  /**
   * Check if a bid is legal according to bridge rules
   * Must be higher level OR same level with higher suit
   */
  const isBidLegal = (bidLevel, suit) => {
    if (!lastRealBid) return true;
    const lastLevel = parseInt(lastRealBid.bid[0], 10);
    const lastSuit = lastRealBid.bid.slice(1);
    if (bidLevel > lastLevel) return true;
    if (bidLevel === lastLevel && suitOrder[suit] > suitOrder[lastSuit]) return true;
    return false;
  };

  const handleLevelClick = (l) => {
    setLevel(l);
  };

  const handleSuitClick = (suit) => {
    if (level) {
      onBid(suit === 'NT' ? `${level}NT` : `${level}${suit}`);
      setLevel(null);
    }
  };

  const handleCallClick = (call) => {
    onBid(call);
    setLevel(null);
  };

  const getSuitClass = (suit) => {
    switch (suit) {
      case '♣': return 'suit-clubs';
      case '♦': return 'suit-diamonds';
      case '♥': return 'suit-hearts';
      case '♠': return 'suit-spades';
      default: return 'suit-nt';
    }
  };

  return (
    <div className="bidding-box" data-testid="bidding-box">
      {/* Level buttons (1-7) */}
      <div className="bidding-box-row" data-testid="bid-levels">
        {levels.map(l => (
          <button
            key={l}
            onClick={() => handleLevelClick(l)}
            disabled={disabled}
            className={`bid-button bid-level-button ${level === l ? 'selected' : ''}`}
            aria-label={`Select level ${l}`}
            data-testid={`bid-level-${l}`}
          >
            {l}
          </button>
        ))}
      </div>

      {/* Suit buttons */}
      <div className="bidding-box-row" data-testid="bid-suits">
        {suits.map(s => {
          const isLegal = !level || isBidLegal(level, s);
          return (
            <button
              key={s}
              onClick={() => handleSuitClick(s)}
              disabled={!level || disabled || !isLegal}
              className="bid-button bid-suit-button"
              aria-label={`Bid ${level || ''} ${s === 'NT' ? 'No Trump' : s}`}
              data-testid={`bid-suit-${s === 'NT' ? 'NT' : s}`}
            >
              <span className={`suit-symbol ${getSuitClass(s)}`}>
                {s === 'NT' ? 'NT' : s}
              </span>
            </button>
          );
        })}
      </div>

      {/* Action buttons (Pass / Dbl / Rdbl) */}
      <div className="bidding-box-row" data-testid="bid-calls">
        <button
          onClick={() => handleCallClick('Pass')}
          disabled={disabled}
          className="bid-button bid-action-button pass-button"
          aria-label="Pass"
          data-testid="bid-call-Pass"
        >
          Pass
        </button>
        <button
          onClick={() => handleCallClick('X')}
          disabled={disabled}
          className="bid-button bid-action-button double-button"
          aria-label="Double"
          data-testid="bid-call-X"
        >
          Dbl
        </button>
        <button
          onClick={() => handleCallClick('XX')}
          disabled={disabled}
          className="bid-button bid-action-button redouble-button"
          aria-label="Redouble"
          data-testid="bid-call-XX"
        >
          Rdbl
        </button>
      </div>
    </div>
  );
}

BiddingBox.displayName = "BiddingBox";
