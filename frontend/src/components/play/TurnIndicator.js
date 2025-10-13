/**
 * TurnIndicator.js - Shows whose turn it is with clear visual indicator
 * Following UI/UX Design Standards - see .claude/UI_UX_DESIGN_STANDARDS.md
 */

import React from 'react';
import './TurnIndicator.css';

/**
 * TurnIndicator Component
 *
 * Displays whose turn it is to play with a prominent, animated indicator.
 * When it's the user's turn, displays large "YOUR TURN!" banner with position.
 *
 * @param {Object} props
 * @param {string} props.currentPlayer - Position code ('N', 'E', 'S', 'W')
 * @param {boolean} props.isUserTurn - True if it's the user's turn
 * @param {string} props.message - Optional custom message
 * @param {string} props.phase - Game phase ('bidding' or 'playing')
 */
export function TurnIndicator({ currentPlayer, isUserTurn, message, phase = 'playing' }) {
  const playerNames = {
    N: 'North',
    E: 'East',
    S: 'South',
    W: 'West'
  };

  // Generate default message if not provided
  const defaultMessage = isUserTurn
    ? `YOUR TURN - ${playerNames[currentPlayer]}`
    : `${playerNames[currentPlayer]}'s Turn`;

  const displayMessage = message || defaultMessage;

  // Add action hint based on phase
  const actionHint = isUserTurn
    ? (phase === 'playing' ? `Play a card from ${playerNames[currentPlayer]}'s hand` : 'Select a bid')
    : `Waiting for ${playerNames[currentPlayer]}...`;

  return (
    <div
      className={`turn-indicator ${isUserTurn ? 'user-turn' : ''}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="turn-indicator-content">
        {isUserTurn && <span className="turn-icon" aria-hidden="true">⏰</span>}
        <div className="turn-text">
          <span className="turn-message">{displayMessage}</span>
          <span className="turn-hint">{actionHint}</span>
        </div>
        {isUserTurn && <span className="turn-icon" aria-hidden="true">⏰</span>}
      </div>
    </div>
  );
}

/**
 * CompactTurnIndicator Component
 *
 * Smaller version for use in position labels
 *
 * @param {Object} props
 * @param {string} props.position - Position code ('N', 'E', 'S', 'W')
 * @param {boolean} props.isActive - True if this position is currently playing
 */
export function CompactTurnIndicator({ position, isActive }) {
  if (!isActive) return null;

  return (
    <span
      className="compact-turn-indicator"
      role="img"
      aria-label={`${position} is currently playing`}
    >
      ◀
    </span>
  );
}

export default TurnIndicator;
