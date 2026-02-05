/**
 * SessionScorePanel - Optional running score display
 *
 * Shows cumulative NS vs EW scores across hands.
 * Hidden by default to reduce cognitive load - users can expand if interested.
 *
 * Features:
 * - Collapsed by default (shows just score badge)
 * - Persists preference to localStorage
 * - No session boundaries or "X of Y" framing
 */

import React, { useState } from 'react';
import './SessionScorePanel.css';

export function SessionScorePanel({ sessionData, onViewHistory }) {
  // Collapsed by default for simpler UX
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('bridge-score-panel-collapsed');
    // Default to collapsed (true) if no preference saved
    return saved !== 'false';
  });

  const handleToggleCollapse = () => {
    const newValue = !isCollapsed;
    setIsCollapsed(newValue);
    localStorage.setItem('bridge-score-panel-collapsed', String(newValue));
  };

  if (!sessionData || !sessionData.active) {
    return null;
  }

  const { session } = sessionData;
  const userOnNS = session.player_position === 'N' || session.player_position === 'S';
  const userScore = userOnNS ? session.ns_score : session.ew_score;
  const opponentScore = userOnNS ? session.ew_score : session.ns_score;

  // Collapsed view - minimal score badge
  if (isCollapsed) {
    return (
      <div className="session-score-panel session-score-panel-collapsed">
        <button
          className="session-collapse-toggle"
          onClick={handleToggleCollapse}
          aria-label="Show running score"
          title="Show running score"
        >
          <span className="collapse-badge">
            Score: {userScore} - {opponentScore}
          </span>
          <span className="collapse-icon">▼</span>
        </button>
      </div>
    );
  }

  // Expanded view - full score details
  const userLabel = userOnNS ? 'You (N-S)' : 'You (E-W)';
  const opponentLabel = userOnNS ? 'Opponents (E-W)' : 'Opponents (N-S)';

  return (
    <div className="session-score-panel">
      <button
        className="session-collapse-toggle session-collapse-expanded"
        onClick={handleToggleCollapse}
        aria-label="Hide running score"
        title="Hide running score"
      >
        <span className="collapse-icon">▲</span>
      </button>

      <div className="session-header">
        <h3 className="session-title">Running Score</h3>
        <span className="hands-played-badge">
          {session.hands_completed} hand{session.hands_completed !== 1 ? 's' : ''} played
        </span>
      </div>

      <div className="session-scores">
        <div className={`partnership-score user-score ${userScore > opponentScore ? 'leading' : ''}`}>
          <div className="score-label">{userLabel}</div>
          <div className="score-value">{userScore}</div>
          {userScore > opponentScore && <div className="leader-badge">Leading</div>}
        </div>

        <div className="score-divider">
          <span className="vs-label">vs</span>
        </div>

        <div className={`partnership-score opponent-score ${opponentScore > userScore ? 'leading' : ''}`}>
          <div className="score-label">{opponentLabel}</div>
          <div className="score-value">{opponentScore}</div>
          {opponentScore > userScore && <div className="leader-badge">Leading</div>}
        </div>
      </div>

      {onViewHistory && session.hands_completed > 0 && (
        <div className="panel-actions">
          <button className="view-history-btn" onClick={onViewHistory}>
            View Hand History
          </button>
        </div>
      )}
    </div>
  );
}
