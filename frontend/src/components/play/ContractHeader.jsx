import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * ContractHeader - Consolidated header showing contract, tricks progress, and bidding summary
 * NEW LAYOUT: Contract on left, 13-block trick progress below it, bidding table on right
 * Follows "Rule of Three" and senior-friendly UX principles
 */
export function ContractHeader({ contract, tricksWon, auction }) {
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
        <div className="flex flex-col">
          <div className="text-3xl font-bold text-white">
            {level}{displayStrain}{doubledText} by {declarerName}
          </div>
        </div>

        {/* 13-Block Tricks Progress Bar */}
        <div className="flex flex-col gap-2 min-w-[500px]">
          {/* Labels above blocks */}
          <div className="flex flex-row justify-between text-sm text-gray-300">
            <span>Won</span>
            <span>Remaining</span>
            <span>Lost</span>
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
                  index === tricksNeeded - 1 && "border-r-2 border-r-white",
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
          <table className="w-full text-base">
            <thead>
              <tr className="text-gray-400">
                <th className="text-left px-2 py-1">N</th>
                <th className="text-left px-2 py-1">E</th>
                <th className="text-left px-2 py-1">S</th>
                <th className="text-left px-2 py-1">W</th>
              </tr>
            </thead>
            <tbody>
              {rounds.map((round, roundIndex) => (
                <tr key={roundIndex} className="text-white">
                  {[0, 1, 2, 3].map(col => (
                    <td key={col} className="px-2 py-1">
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
