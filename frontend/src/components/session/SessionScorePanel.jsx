/**
 * SessionScorePanel - Display current session scoring
 *
 * Shows:
 * - Session progress (hand N of M)
 * - Current scores (NS vs EW)
 * - Current hand dealer and vulnerability
 * - Score leader indicator
 */

import React from 'react';
import './SessionScorePanel.css';

export function SessionScorePanel({ sessionData, onViewHistory }) {
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

  return (
    <div className="session-score-panel">
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
