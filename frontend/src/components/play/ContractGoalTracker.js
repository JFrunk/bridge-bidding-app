/**
 * ContractGoalTracker.js - Shows progress toward making contract
 * Following UI/UX Design Standards - see .claude/UI_UX_DESIGN_STANDARDS.md
 */

import React from 'react';
import './ContractGoalTracker.css';

/**
 * ContractGoalTracker Component
 *
 * Displays contract goal, current progress, and status toward making contract.
 * Visual progress bar with color-coded status (on-track, danger, safe).
 *
 * @param {Object} props
 * @param {Object} props.contract - Contract object {level, strain, declarer, doubled}
 * @param {number} props.tricksWon - Number of tricks declarer side has won
 * @param {number} props.tricksNeeded - Number of tricks needed to make contract (level + 6)
 * @param {number} props.tricksRemaining - Number of tricks left to play (13 - tricks played)
 * @param {string} props.declarerSide - 'NS' or 'EW'
 */
export function ContractGoalTracker({
  contract,
  tricksWon,
  tricksNeeded,
  tricksRemaining,
  declarerSide
}) {
  // Calculate progress percentage
  const progress = (tricksWon / tricksNeeded) * 100;
  const tricksShort = tricksNeeded - tricksWon;

  // Determine status based on tricks remaining
  let status = 'on-track';
  let statusMessage = 'On track to make contract';
  let statusIcon = '✓';
  let progressLabel = `${tricksWon} / ${tricksNeeded}`;
  let outcomeCertain = false;

  if (tricksWon >= tricksNeeded) {
    // Contract already made
    status = 'safe';
    outcomeCertain = true;
    const overtricks = tricksWon - tricksNeeded;
    statusMessage = overtricks > 0
      ? `Contract made with ${overtricks} overtrick${overtricks > 1 ? 's' : ''}`
      : 'Contract made exactly';
    statusIcon = '✓';

    // Update progress label to show outcome
    if (overtricks === 0) {
      progressLabel = 'Contract Made';
    } else {
      progressLabel = `Made +${overtricks}`;
    }
  } else if (tricksShort > tricksRemaining) {
    // Cannot make contract anymore
    status = 'danger';
    outcomeCertain = true;
    const down = tricksShort - tricksRemaining;
    statusMessage = `Down ${down} - cannot make contract`;
    statusIcon = '✗';

    // Update progress label to show outcome
    progressLabel = `Down ${down}`;
  } else if (tricksShort === tricksRemaining) {
    // Must win all remaining tricks
    status = 'danger';
    statusMessage = 'Must win all remaining tricks!';
    statusIcon = '⚠';
  }

  // Format strain display
  const strainDisplay = contract.strain === 'NT' ? 'NT' : contract.strain;
  const doubledText = contract.doubled === 2 ? 'XX' : contract.doubled === 1 ? 'X' : '';

  return (
    <div className="contract-goal-tracker">
      <div className="goal-header">
        <h4>Contract Goal</h4>
        <span className="goal-statement">
          {declarerSide} needs {tricksNeeded} tricks to make {contract.level}{strainDisplay}{doubledText}
        </span>
      </div>

      <div className="progress-section">
        <div className="progress-bar-container">
          <div
            className={`progress-bar-fill ${status} ${outcomeCertain ? 'outcome-certain' : ''}`}
            style={{ width: `${Math.min(progress, 100)}%` }}
            role="progressbar"
            aria-valuenow={tricksWon}
            aria-valuemin={0}
            aria-valuemax={tricksNeeded}
            aria-label={`${tricksWon} of ${tricksNeeded} tricks won`}
          >
            <span className="progress-bar-label">
              {progressLabel}
            </span>
          </div>
        </div>
      </div>

      <div className="goal-details">
        <div className="detail-row">
          <div className="detail-item">
            <span className="detail-label">Tricks Won:</span>
            <span className="detail-value">{tricksWon}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Tricks Remaining:</span>
            <span className="detail-value">{tricksRemaining}</span>
          </div>
        </div>

        <div className={`status-message ${status}`}>
          <span className="status-icon" aria-hidden="true">{statusIcon}</span>
          <span className="status-text">{statusMessage}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * CompactContractGoal Component
 *
 * Minimal version showing just tricks won vs needed
 * For use in constrained spaces
 *
 * @param {Object} props
 * @param {number} props.tricksWon
 * @param {number} props.tricksNeeded
 */
export function CompactContractGoal({ tricksWon, tricksNeeded }) {
  const status = tricksWon >= tricksNeeded ? 'made' : 'playing';

  return (
    <div className={`compact-contract-goal ${status}`}>
      <span className="compact-label">Goal:</span>
      <span className="compact-value">{tricksWon}/{tricksNeeded}</span>
      {status === 'made' && <span className="compact-icon">✓</span>}
    </div>
  );
}

export default ContractGoalTracker;
