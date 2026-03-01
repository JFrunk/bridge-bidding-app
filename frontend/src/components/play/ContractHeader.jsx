import * as React from "react";
import { useState } from "react";
import { BiddingTableGrid } from "../shared/BiddingTableGrid";
import { BidChip } from "../shared/BidChip";
import "../../styles/PlayScreen.css";  // Import contract-bar styles

/**
 * ContractHeader - Compact contract bar per UI Redesign play-mockup-v2.html
 *
 * Layout (HOTFIX 2 - cleaned up, no duplicates):
 * - Left: Contract badge (e.g., "4♠ by South") + "Vuln: Both"
 * - Center: NS/EW trick counts + Need X + Trick X/13
 * - Right: 📋 Bids button only
 *
 * CRITICAL TEXT COLOR RULES:
 * - Spades ♠ / Clubs ♣ / NT: Text must be WHITE (for dark header) or BLACK (for light)
 * - Hearts ♥ / Diamonds ♦: Text must be RED (#d32f2f)
 *
 * Uses shared BiddingTableGrid component for bid history popup (REUSE!)
 */
export function ContractHeader({ contract, tricksWon, auction, dealer, scoreData, vulnerability }) {
  const [showBidHistory, setShowBidHistory] = useState(false);

  if (!contract) return null;

  const { level, strain, declarer, doubled } = contract;
  const doubledText = doubled === 2 ? 'XX' : doubled === 1 ? 'X' : '';

  // Suit symbol for trump display
  const strainSymbol = {
    'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠', 'N': 'NT'
  }[strain] || strain;

  // Display text for strain (spell out NT)
  const displayStrain = strainSymbol;

  // CRITICAL: Text color must respond to suit for readability on DARK header (#2a2a2a)
  // Red suits (hearts/diamonds) = bright red text, Black suits (spades/clubs/NT) = bright white
  const isRedSuit = strain === 'H' || strain === 'D';
  const suitTextColor = isRedSuit ? '#ff6b7a' : '#ffffff';  // Bright red vs white

  // Map declarer to full name
  const declarerName = {
    'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West'
  }[declarer] || declarer;

  // Calculate tricks for text display
  const tricksNeeded = level + 6;
  const tricksWonByPlayer = (tricksWon.N || 0) + (tricksWon.S || 0);
  const tricksWonByOpponents = (tricksWon.E || 0) + (tricksWon.W || 0);
  const totalTricksPlayed = Object.values(tricksWon).reduce((sum, tricks) => sum + tricks, 0);

  // Calculate score from user's (NS) perspective
  const declarerIsNS = declarer === 'N' || declarer === 'S';
  const userScore = scoreData ? (declarerIsNS ? scoreData.score : -scoreData.score) : null;

  return (
    <>
      <div className="contract-bar">
        {/* Left: Contract Badge - CRITICAL: Suit-responsive text color */}
        <div className="contract-bar-left">
          <div className="contract-badge" style={{ color: suitTextColor }}>
            <span className="contract-level">{level}</span>
            <span className="contract-strain">{displayStrain}</span>
            {doubledText && <span className="contract-doubled">{doubledText}</span>}
          </div>
          {/* Meta info - normalized typography */}
          <div className="contract-info-row">
            <span className="info-label">by</span>
            <span className="info-value">{declarerName}</span>
            <span className="info-separator">•</span>
            <span className="info-label">Vuln:</span>
            <span className="info-value">{vulnerability || 'None'}</span>
          </div>
          {/* Score when complete */}
          {scoreData && totalTricksPlayed === 13 && (
            <div className={`contract-score ${userScore >= 0 ? 'positive' : 'negative'}`}>
              {userScore >= 0 ? '+' : ''}{userScore}
            </div>
          )}
        </div>

        {/* Center: Trick Counter - Normalized typography */}
        <div className="trick-counter-text">
          <span className="trick-ns">
            <span className="info-label">NS:</span> <strong>{tricksWonByPlayer}</strong>
          </span>
          <span className="info-separator">•</span>
          <span className="trick-ew">
            <span className="info-label">EW:</span> <strong>{tricksWonByOpponents}</strong>
          </span>
          <span className="info-separator">•</span>
          <span className="trick-need">
            <span className="info-label">Need</span> <strong>{tricksNeeded}</strong>
          </span>
          <span className="info-separator">•</span>
          <span className="trick-current">
            <span className="info-label">Trick</span> <strong>{Math.min(totalTricksPlayed + 1, 13)}/13</strong>
          </span>
        </div>

        {/* Right: Bid History Button */}
        <div className="contract-bar-right">
          <button
            className="bid-history-btn"
            onClick={() => setShowBidHistory(true)}
            aria-label="Show bid history"
          >
            📋 Bids
          </button>
        </div>
      </div>

      {/* Bid History Popup - Uses shared BiddingTableGrid component (REUSE!) */}
      {showBidHistory && (
        <div className="bid-history-overlay" onClick={() => setShowBidHistory(false)}>
          <div className="bid-history-popup" onClick={e => e.stopPropagation()}>
            <div className="bid-history-header">
              <h3>Bidding History</h3>
              <button
                className="bid-history-close"
                onClick={() => setShowBidHistory(false)}
                aria-label="Close bid history"
              >
                ×
              </button>
            </div>
            {/* REUSE: Same component as main bidding phase */}
            <BiddingTableGrid
              auction={auction || []}
              dealer={dealer}
              isComplete={true}
              compact={true}
            />
            <div className="bid-history-contract">
              Final Contract: <BidChip bid={`${level}${strain}${doubledText}`} /> by {declarerName}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
