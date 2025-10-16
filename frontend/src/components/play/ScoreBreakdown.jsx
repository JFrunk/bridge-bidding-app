import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * ScoreBreakdown - Display detailed scoring calculation
 *
 * Shows line-by-line breakdown of how the final score was calculated,
 * with clear labels and explanations for each component.
 *
 * Props:
 *   - breakdown: Object with scoring components (from backend)
 *   - contract: Contract object with level, strain, declarer, doubled
 *   - made: Boolean - whether contract was made
 *   - overtricks: Number of overtricks (if made)
 *   - undertricks: Number of undertricks (if defeated)
 *   - tricksNeeded: Number of tricks needed for contract
 *   - vulnerable: Boolean - whether declarer was vulnerable
 */
export function ScoreBreakdown({
  breakdown,
  contract,
  made,
  overtricks = 0,
  undertricks = 0,
  tricksNeeded,
  vulnerable = false
}) {
  if (!breakdown) return null;

  const doubledText = contract.doubled === 2 ? 'redoubled' : contract.doubled === 1 ? 'doubled' : '';
  const contractStr = `${contract.level}${contract.strain}`;

  // Helper to format score items
  const ScoreItem = ({ label, value, explanation, isTotal = false }) => (
    <div className={cn(
      "flex justify-between items-start gap-4 py-2",
      isTotal && "border-t-2 border-gray-300 mt-2 pt-3 font-bold"
    )}>
      <div className="flex-1">
        <div className={cn(
          "text-base",
          isTotal ? "text-lg font-bold text-gray-900" : "font-medium text-gray-800"
        )}>
          {label}
        </div>
        {explanation && (
          <div className="text-sm text-gray-600 mt-0.5 leading-tight">
            {explanation}
          </div>
        )}
      </div>
      <div className={cn(
        "text-right",
        isTotal ? "text-2xl font-bold" : "text-lg font-semibold",
        value > 0 ? "text-success" : value < 0 ? "text-danger" : "text-gray-500"
      )}>
        {value > 0 ? '+' : ''}{value}
      </div>
    </div>
  );

  // Calculate total
  const total = made
    ? (breakdown.trick_score || 0) +
      (breakdown.game_bonus || 0) +
      (breakdown.slam_bonus || 0) +
      (breakdown.overtrick_score || 0) +
      (breakdown.double_bonus || 0) +
      (breakdown.honors_bonus || 0)
    : -(breakdown.penalty || 0);

  if (made) {
    // Contract made - show positive scoring
    return (
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <h4 className="text-lg font-bold text-gray-900 mb-3">
          Score Breakdown
        </h4>

        <div className="space-y-1">
          {/* Contract tricks */}
          {breakdown.trick_score > 0 && (
            <ScoreItem
              label="Contract Tricks"
              value={breakdown.trick_score}
              explanation={doubledText
                ? `${contractStr} ${doubledText}: ${contract.level} tricks × ${contract.strain === 'NT' || contract.strain === '♥' || contract.strain === '♠' ? '30' : '20'} × ${contract.doubled === 2 ? '4' : '2'}`
                : `${contractStr}: ${contract.level} tricks × ${contract.strain === 'NT' || contract.strain === '♥' || contract.strain === '♠' ? '30' : '20'}${contract.strain === 'NT' ? ' +10 for NT' : ''}`
              }
            />
          )}

          {/* Double/Redouble bonus */}
          {breakdown.double_bonus > 0 && (
            <ScoreItem
              label={contract.doubled === 2 ? "Redouble Bonus" : "Double Bonus"}
              value={breakdown.double_bonus}
              explanation={`For making ${doubledText} contract`}
            />
          )}

          {/* Game bonus */}
          {breakdown.game_bonus > 0 && (
            <ScoreItem
              label={breakdown.game_bonus >= 300 ? "Game Bonus" : "Part-Score Bonus"}
              value={breakdown.game_bonus}
              explanation={
                breakdown.game_bonus >= 300
                  ? `Made game (trick score ≥ 100)${vulnerable ? ', vulnerable' : ', not vulnerable'}`
                  : "Part-score bonus"
              }
            />
          )}

          {/* Slam bonus */}
          {breakdown.slam_bonus > 0 && (
            <ScoreItem
              label={contract.level === 7 ? "Grand Slam Bonus" : "Small Slam Bonus"}
              value={breakdown.slam_bonus}
              explanation={`${contract.level === 7 ? '7-level' : '6-level'} contract${vulnerable ? ', vulnerable' : ', not vulnerable'}`}
            />
          )}

          {/* Overtricks */}
          {overtricks > 0 && (
            <ScoreItem
              label={`Overtricks (${overtricks})`}
              value={breakdown.overtrick_score || 0}
              explanation={
                doubledText
                  ? `${overtricks} extra trick${overtricks > 1 ? 's' : ''} × ${vulnerable ? (contract.doubled === 2 ? '400' : '200') : (contract.doubled === 2 ? '200' : '100')}`
                  : `${overtricks} extra trick${overtricks > 1 ? 's' : ''} × ${contract.strain === 'NT' || contract.strain === '♥' || contract.strain === '♠' ? '30' : '20'}`
              }
            />
          )}

          {/* Honors */}
          {breakdown.honors_bonus > 0 && (
            <ScoreItem
              label="Honors Bonus"
              value={breakdown.honors_bonus}
              explanation={
                breakdown.honors_bonus === 150 && contract.strain === 'NT'
                  ? "All 4 aces in one hand"
                  : breakdown.honors_bonus === 150
                  ? `All 5 trump honors (A-K-Q-J-10 of ${contract.strain}) in one hand`
                  : `4 of 5 trump honors in one hand`
              }
            />
          )}

          {/* Total */}
          <ScoreItem
            label="Total Score"
            value={total}
            isTotal={true}
          />
        </div>
      </div>
    );
  } else {
    // Contract defeated - show penalty
    return (
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <h4 className="text-lg font-bold text-gray-900 mb-3">
          Score Breakdown
        </h4>

        <div className="space-y-1">
          {/* Contract failed */}
          <ScoreItem
            label={`Contract Failed (Down ${undertricks})`}
            value={-breakdown.penalty}
            explanation={
              doubledText
                ? `${undertricks} undertrick${undertricks > 1 ? 's' : ''} ${doubledText}${vulnerable ? ', vulnerable' : ', not vulnerable'}`
                : `${undertricks} undertrick${undertricks > 1 ? 's' : ''} × ${vulnerable ? '100' : '50'} per trick`
            }
          />

          {/* Detailed penalty breakdown for doubled contracts */}
          {doubledText && undertricks > 1 && (
            <div className="ml-4 text-sm text-gray-600 space-y-0.5">
              {vulnerable ? (
                <>
                  <div>• First undertrick: {contract.doubled === 2 ? '400' : '200'}</div>
                  {undertricks > 1 && <div>• Next {undertricks - 1} undertrick{undertricks > 2 ? 's' : ''}: {(undertricks - 1)} × {contract.doubled === 2 ? '600' : '300'}</div>}
                </>
              ) : (
                <>
                  <div>• First undertrick: {contract.doubled === 2 ? '200' : '100'}</div>
                  {undertricks > 1 && undertricks <= 3 && <div>• Next {Math.min(2, undertricks - 1)} undertrick{undertricks > 2 ? 's' : ''}: {Math.min(2, undertricks - 1)} × {contract.doubled === 2 ? '400' : '200'}</div>}
                  {undertricks > 3 && <div>• Remaining {undertricks - 3} undertrick{undertricks > 4 ? 's' : ''}: {undertricks - 3} × {contract.doubled === 2 ? '600' : '300'}</div>}
                </>
              )}
            </div>
          )}

          {/* Total */}
          <ScoreItem
            label="Total Penalty"
            value={-breakdown.penalty}
            isTotal={true}
          />
        </div>
      </div>
    );
  }
}
