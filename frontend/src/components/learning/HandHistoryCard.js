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
  // Format the date for display
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      // Today - show time
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return `${days} days ago`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
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

  // Get result display with color coding
  const getResultDisplay = () => {
    if (!hand.result) return null;

    const made = hand.made;
    let className = 'result-exact';

    if (hand.result.startsWith('+')) {
      className = 'result-overtrick';
    } else if (hand.result.startsWith('-')) {
      className = 'result-undertrick';
    }

    return { text: hand.result, className, made };
  };

  // Get score display
  const getScoreDisplay = () => {
    const score = hand.score || 0;
    if (score === 0) return { text: '0', className: 'score-zero' };
    if (score > 0) return { text: `+${score}`, className: 'score-positive' };
    return { text: `${score}`, className: 'score-negative' };
  };

  const role = getRoleDisplay();
  const result = getResultDisplay();
  const scoreDisplay = getScoreDisplay();

  // Format suit symbols for contract display
  const formatContract = (contract) => {
    if (!contract) return 'Passed Out';
    // Replace suit letters with symbols if needed
    return contract
      .replace(/S(?![A-Za-z])/g, '♠')
      .replace(/H(?![A-Za-z])/g, '♥')
      .replace(/D(?![A-Za-z])/g, '♦')
      .replace(/C(?![A-Za-z])/g, '♣');
  };

  // Get suit color for contract display
  const getSuitColor = (strain) => {
    if (!strain) return '#1f2937'; // Dark gray fallback
    const s = strain.toUpperCase();
    if (s === 'S' || s === '♠') return '#000000';
    if (s === 'H' || s === '♥') return '#dc2626';
    if (s === 'D' || s === '♦') return '#dc2626';
    if (s === 'C' || s === '♣') return '#000000';
    if (s === 'NT' || s === 'N') return '#1f2937'; // Dark gray for NT
    return '#1f2937'; // Dark gray fallback for unknown
  };

  return (
    <div
      className={`hand-history-card ${hand.can_replay ? 'clickable' : 'no-replay'}`}
      onClick={() => hand.can_replay && onClick && onClick(hand)}
    >
      {/* Contract & Result Row */}
      <div className="hand-card-main">
        <div className="hand-contract" style={{ color: getSuitColor(hand.contract_strain) }}>
          {formatContract(hand.contract)}
        </div>

        {result && (
          <div className={`hand-result ${result.className}`}>
            {result.text}
          </div>
        )}
      </div>

      {/* Details Row */}
      <div className="hand-card-details">
        <span className={`hand-role ${role.className}`}>
          {role.text}
        </span>

        <span className={`hand-score ${scoreDisplay.className}`}>
          {scoreDisplay.text}
        </span>

        <span className="hand-date">
          {formatDate(hand.played_at)}
        </span>
      </div>

      {/* Replay indicator */}
      {hand.can_replay && (
        <div className="hand-replay-indicator">
          <span className="replay-icon">🔍</span>
          <span className="replay-text">Analyze</span>
        </div>
      )}
    </div>
  );
};

export default HandHistoryCard;
