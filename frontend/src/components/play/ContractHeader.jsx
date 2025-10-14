import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * ContractHeader - Consolidated header showing contract, tricks progress, and bidding summary
 * NEW LAYOUT: Contract on left, 13-block trick progress below it, bidding table on right
 * Follows "Rule of Three" and senior-friendly UX principles
 * Shows score when hand is complete (totalTricksPlayed === 13)
 */
export function ContractHeader({ contract, tricksWon, auction, scoreData }) {
  if (!contract) return null;

  const { level, strain, declarer, doubled } = contract;
  const doubledText = doubled === 2 ? 'XX' : doubled === 1 ? 'X' : '';
  const displayStrain = strain === 'N' ? 'NT' : strain;

  // Map declarer to full name
  const declarerName = {
    'N': 'North',
    'E': 'East',
    'S': 'South',
    'W': 'West'
  }[declarer] || declarer;

  // Calculate tricks for 13-block progress bar
  const tricksNeeded = level + 6;
  const declarerSide = (declarer === 'N' || declarer === 'S') ? 'NS' : 'EW';
  const tricksWonBySide = declarerSide === 'NS'
    ? (tricksWon.N || 0) + (tricksWon.S || 0)
    : (tricksWon.E || 0) + (tricksWon.W || 0);
  const totalTricksPlayed = Object.values(tricksWon).reduce((sum, tricks) => sum + tricks, 0);
  const tricksRemaining = 13 - totalTricksPlayed;
  const tricksLost = 13 - tricksWonBySide - tricksRemaining;

  // Create 13 blocks array with state (won/remaining/lost)
  const blocks = Array.from({ length: 13 }, (_, i) => {
    if (i < tricksWonBySide) return 'won';
    if (i >= 13 - tricksLost) return 'lost';
    return 'remaining';
  });

  // Group auction into rounds (4 bids per round: N, E, S, W)
  const rounds = [];
  if (auction) {
    for (let i = 0; i < auction.length; i += 4) {
      rounds.push(auction.slice(i, i + 4));
    }
  }

  return (
    <div className="flex flex-row gap-6 p-4 bg-bg-secondary rounded-lg">
      {/* LEFT SECTION: Contract + 13-Block Progress Bar */}
      <div className="flex flex-col gap-4">
        {/* Contract Display */}
        <div className="flex flex-col gap-2">
          <div className="text-3xl font-bold text-white">
            {level}{displayStrain}{doubledText} by {declarerName}
          </div>
          {/* Score Display - Only shown when hand is complete */}
          {scoreData && totalTricksPlayed === 13 && (
            <div className={cn(
              "flex items-center gap-3 px-4 py-2 rounded-md border-2 w-fit",
              scoreData.score >= 0 ? "bg-green-900/30 border-success" : "bg-red-900/30 border-danger"
            )}>
              <span className="text-lg font-medium text-gray-300">Score:</span>
              <span className={cn(
                "text-2xl font-bold",
                scoreData.score >= 0 ? "text-success" : "text-danger"
              )}>
                {scoreData.score >= 0 ? '+' : ''}{scoreData.score}
              </span>
              <span className={cn(
                "text-base font-medium",
                scoreData.made ? "text-success" : "text-danger"
              )}>
                ({scoreData.result})
              </span>
            </div>
          )}
        </div>

        {/* 13-Block Tricks Progress Bar */}
        <div className="flex flex-col gap-2 min-w-[500px]">
          {/* Labels with counts */}
          <div className="flex flex-row justify-between text-sm text-gray-300">
            <div className="flex flex-col items-start">
              <span className="font-bold">Won</span>
              <span className="text-lg text-white">{tricksWonBySide}</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="font-bold">Remaining</span>
              <span className="text-lg text-white">{tricksRemaining}</span>
            </div>
            <div className="flex flex-col items-end">
              <span className="font-bold">Lost</span>
              <span className="text-lg text-white">{tricksLost}</span>
            </div>
          </div>

          {/* Goal indicator above bar */}
          <div className="flex flex-row h-8 relative">
            {blocks.map((state, index) => (
              <div
                key={index}
                className="flex-1 flex items-start justify-center"
              >
                {index === tricksNeeded - 1 && (
                  <div className="text-xl font-bold text-white">↓ {tricksNeeded}</div>
                )}
              </div>
            ))}
          </div>

          {/* 13 Blocks with vertical dividers */}
          <div className="flex flex-row h-12 border-2 border-gray-600 rounded-md overflow-hidden">
            {blocks.map((state, index) => (
              <div
                key={index}
                className={cn(
                  "flex-1 flex items-center justify-center transition-colors duration-300",
                  "border-r border-gray-600 last:border-r-0",
                  // Bold border at trick needed line
                  index === tricksNeeded - 1 && "border-r-4 border-r-white",
                  // Colors based on state
                  state === 'won' && "bg-success",
                  state === 'remaining' && "bg-bg-tertiary",
                  state === 'lost' && "bg-danger"
                )}
                aria-label={`Trick ${index + 1}: ${state}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT SECTION: Bidding Table */}
      <div className="flex flex-col flex-1 min-w-[200px] max-w-[300px]">
        <div className="text-base font-bold text-gray-300 mb-2">Bidding</div>
        <div className="flex-1 overflow-y-auto max-h-32">
          <table className="w-full text-base border-collapse">
            <thead>
              <tr className="text-gray-400 border-b border-gray-600">
                <th className="text-left px-2 py-1 border-r border-gray-600">N</th>
                <th className="text-left px-2 py-1 border-r border-gray-600">E</th>
                <th className="text-left px-2 py-1 border-r border-gray-600">S</th>
                <th className="text-left px-2 py-1">W</th>
              </tr>
            </thead>
            <tbody>
              {rounds.map((round, roundIndex) => (
                <tr key={roundIndex} className="text-white border-b border-gray-700">
                  {[0, 1, 2, 3].map(col => (
                    <td key={col} className={cn("px-2 py-1", col < 3 && "border-r border-gray-700")}>
                      {round[col]?.bid || '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
