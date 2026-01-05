/**
 * HandHistoryCard Component - Displays a single hand from history
 *
 * Shows:
 * - Contract and result
 * - User's role (declarer/defender/dummy)
 * - Score
 * - Click to open replay modal
 *
 * Styled to match the dashboard theme.
 */

import React from 'react';
import './HandHistoryCard.css';

const HandHistoryCard = ({ hand, onClick }) => {
  // Format relative time display (e.g., "2 min ago", "1h ago", "Yesterday")
  const getRelativeTime = () => {
    if (!hand.played_at) return null;

    const now = new Date();
    const played = new Date(hand.played_at);
    const diffMs = now - played;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;

    // Format as date for older hands
    return played.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Get role display
  const getRoleDisplay = () => {
    if (hand.user_was_declarer) {
      return { text: 'Declarer', className: 'role-declarer' };
    } else if (hand.user_was_dummy) {
      return { text: 'Dummy', className: 'role-dummy' };
    } else {
      return { text: 'Defender', className: 'role-defender' };
    }
  };

  // Get result display from user's perspective
  const getResultDisplay = () => {
    const tricksTaken = hand.tricks_taken;
    const tricksNeeded = hand.tricks_needed;

    if (tricksTaken === undefined || tricksNeeded === undefined) {
      return hand.made ? { text: 'Made', className: 'result-made' } : { text: 'Down', className: 'result-down' };
    }

    if (hand.made) {
      const over = tricksTaken - tricksNeeded;
      if (over > 0) {
        return { text: `Made +${over}`, className: 'result-made' };
      }
      return { text: 'Made', className: 'result-made' };
    } else {
      const down = tricksNeeded - tricksTaken;
      return { text: `Down ${down}`, className: 'result-down' };
    }
  };

  // Get tricks display (X/Y format)
  const getTricksDisplay = () => {
    const tricksTaken = hand.tricks_taken;
    const tricksNeeded = hand.tricks_needed;
    if (tricksTaken === undefined || tricksNeeded === undefined) return null;
    return `${tricksTaken}/${tricksNeeded}`;
  };

  // Get score display from NS perspective
  const getScoreDisplay = () => {
    let score = hand.score || 0;

    // Convert to NS perspective if declarer was EW
    const declarer = hand.contract_declarer;
    if (declarer === 'E' || declarer === 'W') {
      score = -score;
    }

    if (score === 0) return { text: '0', className: 'score-zero' };
    if (score > 0) return { text: `+${score}`, className: 'score-positive' };
    return { text: `${score}`, className: 'score-negative' };
  };

  // Get declarer name
  const getDeclarerName = () => {
    const d = hand.contract_declarer;
    if (d === 'N') return 'North';
    if (d === 'S') return 'South';
    if (d === 'E') return 'East';
    if (d === 'W') return 'West';
    return d;
  };

  const role = getRoleDisplay();
  const result = getResultDisplay();
  const tricksDisplay = getTricksDisplay();
  const scoreDisplay = getScoreDisplay();
  const relativeTime = getRelativeTime();

  // Format contract display (e.g., "3NTX by East")
  const formatContract = (contract) => {
    if (!contract) return 'Passed Out';
    return contract;
  };

  // Get suit color for contract display
  const getSuitColor = (strain) => {
    if (!strain) return '#1f2937';
    const s = strain.toUpperCase();
    if (s === 'S' || s === '♠') return '#000000';
    if (s === 'H' || s === '♥') return '#dc2626';
    if (s === 'D' || s === '♦') return '#dc2626';
    if (s === 'C' || s === '♣') return '#000000';
    return '#1f2937';
  };

  return (
    <div
      className={`hand-history-card ${hand.can_replay ? 'clickable' : 'no-replay'}`}
      onClick={() => hand.can_replay && onClick && onClick(hand)}
    >
      {/* Main content area */}
      <div className="hand-card-content">
        {/* Contract line - e.g., "3NTX by East" */}
        <div className="hand-contract-line" style={{ color: getSuitColor(hand.contract_strain) }}>
          {formatContract(hand.contract)}
        </div>

        {/* Role and time badges */}
        <div className="hand-meta-row">
          <div className={`hand-role ${role.className}`}>
            {role.text}
          </div>
          {relativeTime && (
            <span className="hand-time">{relativeTime}</span>
          )}
        </div>

        {/* Result with tricks - e.g., "Down 3 (6/9)" */}
        <div className="hand-result-line">
          <span className={`hand-result ${result.className}`}>
            {result.text}
          </span>
          {tricksDisplay && (
            <span className="hand-tricks">({tricksDisplay})</span>
          )}
        </div>

        {/* Score from user's perspective */}
        <div className={`hand-score ${scoreDisplay.className}`}>
          {scoreDisplay.text}
        </div>
      </div>

      {/* Review button - prominent CTA */}
      {hand.can_replay && (
        <button
          className="hand-review-btn"
          onClick={(e) => {
            e.stopPropagation();
            onClick && onClick(hand);
          }}
        >
          Review
        </button>
      )}
    </div>
  );
};

export default HandHistoryCard;
