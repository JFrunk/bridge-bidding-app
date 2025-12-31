/**
 * SessionScorePanel - Display current session scoring
 *
 * Shows:
 * - Session progress (hand N of M)
 * - Current scores (NS vs EW)
 * - Current hand dealer and vulnerability
 * - Score leader indicator
 *
 * Features:
 * - Collapsible panel (persists preference to localStorage)
 * - Collapsed state shows just progress badge
 */

import React, { useState } from 'react';
import './SessionScorePanel.css';

export function SessionScorePanel({ sessionData, onViewHistory }) {
  // Collapse state - persisted to localStorage
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('bridge-session-panel-collapsed');
    return saved === 'true';
  });

  const handleToggleCollapse = () => {
    const newValue = !isCollapsed;
    setIsCollapsed(newValue);
    localStorage.setItem('bridge-session-panel-collapsed', String(newValue));
  };

  if (!sessionData || !sessionData.active) {
    return null;
  }

  const { session } = sessionData;
  const progress = (session.hands_completed / session.max_hands) * 100;
  const userOnNS = session.player_position === 'N' || session.player_position === 'S';
  const userScore = userOnNS ? session.ns_score : session.ew_score;
  const opponentScore = userOnNS ? session.ew_score : session.ns_score;
  const userLabel = userOnNS ? 'North-South (You)' : 'East-West (You)';
  const opponentLabel = userOnNS ? 'East-West' : 'North-South';

  // Collapsed view - just show progress badge
  if (isCollapsed) {
    return (
      <div className="session-score-panel session-score-panel-collapsed">
        <button
          className="session-collapse-toggle"
          onClick={handleToggleCollapse}
          aria-label="Expand session panel"
          title="Expand session panel"
        >
          <span className="collapse-badge">
            Hand {session.hand_number}/{session.max_hands}
          </span>
          <span className="collapse-score">
            {userScore} - {opponentScore}
          </span>
          <span className="collapse-icon">▼</span>
        </button>
      </div>
    );
  }

  return (
    <div className="session-score-panel">
      <button
        className="session-collapse-toggle session-collapse-expanded"
        onClick={handleToggleCollapse}
        aria-label="Collapse session panel"
        title="Collapse session panel"
      >
        <span className="collapse-icon">▲</span>
      </button>

      <div className="session-header">
        <div className="session-title">
          <h3>Chicago Bridge Session</h3>
          {session.session_type === 'chicago' && (
            <span className="session-type-badge">4-Hand Game</span>
          )}
        </div>
        <div className="session-progress">
          <div className="progress-label">
            Hand {session.hand_number} of {session.max_hands}
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="session-scores">
        <div className={`partnership-score user-score ${userScore > opponentScore ? 'leading' : ''}`}>
          <div className="score-label">{userLabel}</div>
          <div className="score-value">{userScore}</div>
          {userScore > opponentScore && <div className="leader-badge">↑ Leading</div>}
        </div>

        <div className="score-divider">
          <span className="vs-label">vs</span>
          <span className="score-difference">
            {Math.abs(userScore - opponentScore) > 0 &&
              `±${Math.abs(userScore - opponentScore)}`}
          </span>
        </div>

        <div className={`partnership-score opponent-score ${opponentScore > userScore ? 'leading' : ''}`}>
          <div className="score-label">{opponentLabel}</div>
          <div className="score-value">{opponentScore}</div>
          {opponentScore > userScore && <div className="leader-badge">↑ Leading</div>}
        </div>
      </div>

      <div className="current-hand-info">
        <div className="info-item">
          <span className="info-label">Dealer:</span>
          <span className="info-value">{session.dealer}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Vulnerability:</span>
          <span className={`info-value vuln-${session.vulnerability.toLowerCase()}`}>
            {session.vulnerability}
          </span>
        </div>
        {onViewHistory && session.hands_completed > 0 && (
          <button className="view-history-btn" onClick={onViewHistory}>
            View History ({session.hands_completed} hands)
          </button>
        )}
      </div>
    </div>
  );
}
