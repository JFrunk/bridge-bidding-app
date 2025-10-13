import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * ContractHeader - Consolidated header showing contract, tricks progress, and bidding summary
 * Follows "Rule of Three" and senior-friendly UX principles
 * Designed as SECONDARY visual hierarchy (non-distracting)
 */
export function ContractHeader({ contract, tricksWon, auction }) {
  if (!contract) return null;

  const { level, strain, declarer, doubled } = contract;
  const doubledText = doubled === 2 ? 'XX' : doubled === 1 ? 'X' : '';
  const displayStrain = strain === 'N' ? 'NT' : strain;

  // Calculate tricks for progress bar
  const tricksNeeded = level + 6;
  const declarerSide = (declarer === 'N' || declarer === 'S') ? 'NS' : 'EW';
  const tricksWonBySide = declarerSide === 'NS'
    ? (tricksWon.N || 0) + (tricksWon.S || 0)
    : (tricksWon.E || 0) + (tricksWon.W || 0);
  const totalTricksPlayed = Object.values(tricksWon).reduce((sum, tricks) => sum + tricks, 0);
  const tricksRemaining = 13 - totalTricksPlayed;
  const tricksLost = 13 - tricksWonBySide - tricksRemaining;

  return (
    <div className="flex flex-row items-stretch gap-6 p-4 bg-bg-secondary rounded-lg">
      {/* Unified Tricks Progress Bar - Visual indicator of contract progress */}
      <div className="flex flex-col justify-center min-w-[200px]">
        <div className="flex flex-row h-12 rounded-md overflow-hidden border border-gray-600">
          {/* Won (green left) */}
          <div
            className="bg-success flex items-center justify-center text-white font-bold"
            style={{ width: `${(tricksWonBySide / 13) * 100}%` }}
            aria-label={`${tricksWonBySide} tricks won`}
          >
            {tricksWonBySide > 0 && <span className="text-sm">{tricksWonBySide}</span>}
          </div>
          {/* Remaining (dark center) */}
          <div
            className="bg-bg-tertiary flex items-center justify-center text-gray-400"
            style={{ width: `${(tricksRemaining / 13) * 100}%` }}
            aria-label={`${tricksRemaining} tricks remaining`}
          >
            {tricksRemaining > 0 && <span className="text-sm">{tricksRemaining}</span>}
          </div>
          {/* Lost (red right) */}
          <div
            className="bg-danger flex items-center justify-center text-white font-bold"
            style={{ width: `${(tricksLost / 13) * 100}%` }}
            aria-label={`${tricksLost} tricks lost`}
          >
            {tricksLost > 0 && <span className="text-sm">{tricksLost}</span>}
          </div>
        </div>
      </div>

      {/* Contract Display - Large, prominent */}
      <div className="flex flex-col justify-center items-center min-w-[120px]">
        <div className="text-3xl font-bold text-white">
          {level}{displayStrain}{doubledText}
        </div>
        <div className="text-base text-gray-300">
          by {declarer}
        </div>
      </div>

      {/* Tricks Summary - Vertical stack */}
      <div className="flex flex-col justify-center gap-1">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400 w-20">Won:</span>
          <span className="text-base text-white font-bold">{tricksWonBySide}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400 w-20">Lost:</span>
          <span className="text-base text-white font-bold">{tricksLost}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400 w-20">Remaining:</span>
          <span className="text-base text-white font-bold">{tricksRemaining}</span>
        </div>
      </div>

      {/* Bidding Summary - Compact, scrollable */}
      <div className="flex flex-col flex-1 min-w-[150px] max-w-[200px]">
        <div className="text-sm font-bold text-gray-300 mb-2">Bidding</div>
        <div className="flex-1 overflow-y-auto max-h-24 space-y-0.5">
          {auction && auction.map((bidObject, index) => {
            const playerIndex = index % 4;
            const playerLabel = ['N', 'E', 'S', 'W'][playerIndex];
            return (
              <div key={index} className="flex items-center gap-2 text-xs">
                <span className="text-gray-400 w-4">{playerLabel}</span>
                <span className="text-white">{bidObject.bid}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
