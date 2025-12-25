/**
 * RecentPlayDecisionsCard Component - Play Feedback System
 *
 * Displays the user's recent play decisions (last 10) with:
 * - Correctness indicator (optimal/good/suboptimal/blunder)
 * - User's card vs optimal card (if different)
 * - Quality score
 * - Contract and trick info
 * - Helpful hint on expand
 *
 * Mirrors RecentDecisionsCard structure for consistency
 */

import React, { useState } from 'react';
import './RecentPlayDecisionsCard.css';

const RecentPlayDecisionsCard = ({ decisions }) => {
  const [expandedId, setExpandedId] = useState(null);

  if (!decisions || decisions.length === 0) {
    return (
      <div className="dashboard-card recent-play-decisions-card">
        <div className="dashboard-card-header">
          <h3 className="dashboard-card-title">Recent Card Plays</h3>
          <span className="dashboard-card-icon">🃏</span>
        </div>
        <div className="dashboard-card-body">
          <div className="empty-decisions">
            <div className="empty-decisions-icon">🎴</div>
            <p className="empty-decisions-text">
              No play decisions recorded yet. Play through hands to see your card play feedback here!
            </p>
          </div>
        </div>
      </div>
    );
  }

  const toggleExpanded = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="dashboard-card recent-play-decisions-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Recent Card Plays</h3>
        <span className="dashboard-card-icon">🃏</span>
      </div>
      <div className="dashboard-card-body">
        <div className="decisions-list">
          {decisions.map((decision) => (
            <PlayDecisionItem
              key={decision.id}
              decision={decision}
              isExpanded={expandedId === decision.id}
              onToggle={() => toggleExpanded(decision.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

const PlayDecisionItem = ({ decision, isExpanded, onToggle }) => {
  // Determine icon and color based on rating
  const getRatingDisplay = (rating) => {
    switch (rating) {
      case 'optimal':
        return { icon: '✓', color: '#10b981', bgColor: '#d1fae5', label: 'Optimal' };
      case 'good':
        return { icon: '○', color: '#3b82f6', bgColor: '#dbeafe', label: 'Good' };
      case 'suboptimal':
        return { icon: '⚠', color: '#f59e0b', bgColor: '#fef3c7', label: 'Suboptimal' };
      case 'blunder':
        return { icon: '✗', color: '#ef4444', bgColor: '#fee2e2', label: 'Blunder' };
      case 'illegal':
        return { icon: '⛔', color: '#dc2626', bgColor: '#fecaca', label: 'Illegal' };
      default:
        return { icon: '?', color: '#6b7280', bgColor: '#f3f4f6', label: 'Unknown' };
    }
  };

  const display = getRatingDisplay(decision.rating);

  // Format card display
  const cardDisplay = decision.user_card === decision.optimal_card
    ? decision.user_card
    : decision.optimal_card
      ? `${decision.user_card} → ${decision.optimal_card}`
      : decision.user_card;

  // Format score display
  const scoreDisplay = decision.score != null ? decision.score.toFixed(1) : '—';

  // Get score color
  const getScoreColor = (score) => {
    if (score >= 9) return '#10b981';
    if (score >= 7) return '#3b82f6';
    if (score >= 5) return '#f59e0b';
    return '#ef4444';
  };

  const scoreColor = decision.score != null ? getScoreColor(decision.score) : '#6b7280';

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`play-decision-item ${isExpanded ? 'expanded' : ''}`}>
      <div className="play-decision-item-main" onClick={onToggle}>
        {/* Rating indicator */}
        <div
          className="play-decision-rating"
          style={{
            color: display.color,
            backgroundColor: display.bgColor
          }}
        >
          {display.icon}
        </div>

        {/* Card display */}
        <div className="play-decision-card">
          <div className="card-text">{cardDisplay}</div>
          {decision.contract && (
            <div className="card-context">{decision.contract} • Trick {decision.trick_number}</div>
          )}
        </div>

        {/* Score */}
        <div className="play-decision-score" style={{ color: scoreColor }}>
          <div className="score-value">{scoreDisplay}</div>
          <div className="score-label">/10</div>
        </div>

        {/* Timestamp */}
        <div className="play-decision-time">
          {formatTimestamp(decision.timestamp)}
        </div>

        {/* Expand indicator */}
        <div className="play-decision-expand">
          {isExpanded ? '▼' : '▶'}
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="play-decision-item-details">
          {decision.feedback && (
            <div className="play-decision-hint">
              <div className="hint-icon">💡</div>
              <div className="hint-text">{decision.feedback}</div>
            </div>
          )}

          <div className="play-decision-metadata">
            <div className="metadata-item">
              <span className="metadata-label">Position:</span>
              <span className="metadata-value">{decision.position}</span>
            </div>
            {decision.tricks_cost > 0 && (
              <div className="metadata-item">
                <span className="metadata-label">Tricks Cost:</span>
                <span className="metadata-value tricks-cost">-{decision.tricks_cost}</span>
              </div>
            )}
            <div className="metadata-item">
              <span className="metadata-label">Rating:</span>
              <span className={`metadata-value rating-${decision.rating}`}>
                {display.label}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecentPlayDecisionsCard;
