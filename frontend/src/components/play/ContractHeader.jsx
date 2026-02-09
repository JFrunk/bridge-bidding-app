import * as React from "react";
import { useState } from "react";

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
 * - Hearts ♥ / Diamonds ♦: Text must be RED (#c41e3a)
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

  // CRITICAL: Text color must respond to suit for readability
  // Red suits (hearts/diamonds) = red text, Black suits (spades/clubs/NT) = white text (on dark bg)
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

  // Build bidding history grid - same logic as BiddingTable in App.js
  // Columns are always [North, East, South, West] = indices [0, 1, 2, 3]
  // Dealer starts on row 0 in their column
  // When North column (0) is reached, move to next row
  const players = ['North', 'East', 'South', 'West'];
  const dealerFull = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' }[dealer] || dealer;
  const dealerShort = { 'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W', 'N': 'N', 'E': 'E', 'S': 'S', 'W': 'W' }[dealer] || 'N';
  const dealerIndex = players.indexOf(dealerFull);

  const grid = [];
  let currentRow = 0;
  let currentCol = dealerIndex >= 0 ? dealerIndex : 0; // Start at dealer's column

  for (let i = 0; i < (auction?.length || 0); i++) {
    const bid = auction[i];

    // Ensure row exists
    if (!grid[currentRow]) {
      grid[currentRow] = [null, null, null, null];
    }

    // Place bid in current position
    grid[currentRow][currentCol] = bid;

    // Move to next column (wrapping around)
    currentCol = (currentCol + 1) % 4;

    // If we just wrapped to North column (column 0), move to next row
    if (currentCol === 0 && i < auction.length - 1) {
      currentRow++;
    }
  }

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
            <span className="info-label">Trick</span> <strong>{totalTricksPlayed + 1}/13</strong>
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

      {/* Bid History Popup/Overlay - CRITICAL: Force black text on white background */}
      {showBidHistory && (
        <div className="bid-history-overlay" onClick={() => setShowBidHistory(false)}>
          <div className="bid-history-popup" onClick={e => e.stopPropagation()} style={{ color: '#1a1a1a' }}>
            <div className="bid-history-header">
              <h3 style={{ color: '#1a1a1a' }}>Bidding History</h3>
              <button
                className="bid-history-close"
                onClick={() => setShowBidHistory(false)}
                aria-label="Close bid history"
              >
                ×
              </button>
            </div>
            <table className="bid-history-table">
              <thead>
                <tr>
                  <th style={{ color: '#1a1a1a' }}>N{dealerShort === 'N' ? ' (D)' : ''}</th>
                  <th style={{ color: '#1a1a1a' }}>E{dealerShort === 'E' ? ' (D)' : ''}</th>
                  <th style={{ color: '#1a1a1a' }}>S{dealerShort === 'S' ? ' (D)' : ''}</th>
                  <th style={{ color: '#1a1a1a' }}>W{dealerShort === 'W' ? ' (D)' : ''}</th>
                </tr>
              </thead>
              <tbody>
                {grid.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {[0, 1, 2, 3].map(col => (
                      <td key={col} style={{ color: '#1a1a1a' }}>{row[col]?.bid || ''}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="bid-history-contract" style={{ color: '#1a6b3c' }}>
              Final Contract: <span style={{ color: isRedSuit ? '#c41e3a' : '#1a1a1a' }}>{level}{displayStrain}{doubledText}</span> by {declarerName}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
