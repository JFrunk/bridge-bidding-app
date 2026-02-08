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
 * CRITICAL SCORING PERSPECTIVE LOGIC:
 * - Backend returns scores from DECLARER's perspective (positive = made, negative = went down)
 * - User always plays South (NS team)
 * - MUST convert to user's NS perspective for display
 */
export function ContractHeader({ contract, tricksWon, auction, dealer, scoreData, vulnerability }) {
  const [showBidHistory, setShowBidHistory] = useState(false);

  if (!contract) return null;

  const { level, strain, declarer, doubled } = contract;
  const doubledText = doubled === 2 ? 'XX' : doubled === 1 ? 'X' : '';
  const displayStrain = strain === 'N' ? 'NT' : strain;

  // Suit symbol for trump display
  const strainSymbol = {
    'C': '♣', 'D': '♦', 'H': '♥', 'S': '♠', 'N': 'NT'
  }[strain] || strain;

  const strainClass = {
    'C': 'suit-club', 'D': 'suit-diamond', 'H': 'suit-heart', 'S': 'suit-spade', 'N': ''
  }[strain] || '';

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

  // Build bidding history rounds
  const positions = ['N', 'E', 'S', 'W'];
  const dealerMap = { 'North': 'N', 'East': 'E', 'South': 'S', 'West': 'W', 'N': 'N', 'E': 'E', 'S': 'S', 'W': 'W' };
  const dealerPos = dealerMap[dealer] || 'N';
  const dealerIndex = positions.indexOf(dealerPos);

  const rounds = [];
  if (auction && auction.length > 0) {
    let currentRow = [null, null, null, null];
    let colIndex = dealerIndex;

    for (let i = 0; i < auction.length; i++) {
      currentRow[colIndex] = auction[i];
      colIndex = (colIndex + 1) % 4;

      if (colIndex === dealerIndex && i < auction.length - 1) {
        rounds.push(currentRow);
        currentRow = [null, null, null, null];
      }
    }

    if (currentRow.some(cell => cell !== null)) {
      rounds.push(currentRow);
    }
  }

  return (
    <>
      <div className="contract-bar">
        {/* Left: Contract + Meta */}
        <div className="contract-bar-left">
          <div className="contract-badge">
            <span className="contract-level">{level}</span>
            <span className={`contract-strain ${strainClass}`}>{displayStrain}</span>
            {doubledText && <span className="contract-doubled">{doubledText}</span>}
          </div>
          <div className="contract-meta">
            <span className="contract-declarer">by {declarerName}</span>
            {vulnerability && (
              <span className="contract-vuln">Vuln: {vulnerability}</span>
            )}
          </div>
          {/* Score when complete */}
          {scoreData && totalTricksPlayed === 13 && (
            <div className={`contract-score ${userScore >= 0 ? 'positive' : 'negative'}`}>
              {userScore >= 0 ? '+' : ''}{userScore}
            </div>
          )}
        </div>

        {/* Center: Trick Counter - Simple Text */}
        <div className="trick-counter-text">
          <span className="trick-ns">
            <strong>NS: {tricksWonByPlayer}</strong>
          </span>
          <span className="trick-divider">|</span>
          <span className="trick-ew">
            <strong>EW: {tricksWonByOpponents}</strong>
          </span>
          <span className="trick-divider">|</span>
          <span className="trick-need">Need {tricksNeeded}</span>
          <span className="trick-divider">|</span>
          <span className="trick-current">Trick {totalTricksPlayed + 1}/13</span>
        </div>

        {/* Right: Bid History Button only (Trump/Trick shown in contract badge and center) */}
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

      {/* Bid History Popup/Overlay */}
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
            <table className="bid-history-table">
              <thead>
                <tr>
                  <th>N{dealerPos === 'N' ? ' (D)' : ''}</th>
                  <th>E{dealerPos === 'E' ? ' (D)' : ''}</th>
                  <th>S{dealerPos === 'S' ? ' (D)' : ''}</th>
                  <th>W{dealerPos === 'W' ? ' (D)' : ''}</th>
                </tr>
              </thead>
              <tbody>
                {rounds.map((round, roundIndex) => (
                  <tr key={roundIndex}>
                    {[0, 1, 2, 3].map(col => (
                      <td key={col}>{round[col]?.bid || '-'}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="bid-history-contract">
              Final Contract: {level}{displayStrain}{doubledText} by {declarerName}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
