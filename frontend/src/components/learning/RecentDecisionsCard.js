/**
 * RecentDecisionsCard Component - Phase 1: Bidding Feedback
 *
 * Displays the user's recent bidding decisions (last 10) with:
 * - Correctness indicator (✓ ⚠ ✗)
 * - User's bid vs optimal bid (if different)
 * - Quality score
 * - Key concept
 * - Helpful hint on hover/click
 *
 * Designed to match the existing dashboard card styling
 */

import React, { useState } from 'react';
import './RecentDecisionsCard.css';
import { TermHighlight } from '../glossary';

const RecentDecisionsCard = ({ decisions }) => {
  const [expandedId, setExpandedId] = useState(null);

  if (!decisions || decisions.length === 0) {
    return (
      <div className="dashboard-card recent-decisions-card">
        <div className="dashboard-card-header">
          <h3 className="dashboard-card-title">Recent Bidding Decisions</h3>
          <span className="dashboard-card-icon">📝</span>
        </div>
        <div className="dashboard-card-body">
          <div className="empty-decisions">
            <div className="empty-decisions-icon">🎯</div>
            <p className="empty-decisions-text">
              No decisions recorded yet. Play some hands to see your bidding feedback here!
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
    <div className="dashboard-card recent-decisions-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Recent Bidding Decisions</h3>
        <span className="dashboard-card-icon">📝</span>
      </div>
      <div className="dashboard-card-body">
        <div className="decisions-list">
          {decisions.map((decision) => (
            <DecisionItem
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

const DecisionItem = ({ decision, isExpanded, onToggle }) => {
  // Determine icon and color based on correctness
  const getCorrectnessDisplay = (correctness) => {
    switch (correctness) {
      case 'optimal':
        return { icon: '✓', color: '#10b981', bgColor: '#d1fae5' };
      case 'acceptable':
        return { icon: 'ⓘ', color: '#3b82f6', bgColor: '#dbeafe' };
      case 'suboptimal':
        return { icon: '⚠', color: '#f59e0b', bgColor: '#fef3c7' };
      case 'error':
        return { icon: '✗', color: '#ef4444', bgColor: '#fee2e2' };
      default:
        return { icon: '?', color: '#6b7280', bgColor: '#f3f4f6' };
    }
  };

  const display = getCorrectnessDisplay(decision.correctness);

  // Format bid display
  const bidDisplay = decision.user_bid === decision.optimal_bid
    ? decision.user_bid
    : `${decision.user_bid} → ${decision.optimal_bid}`;

  // Format score display
  const scoreDisplay = decision.score ? decision.score.toFixed(1) : '—';

  // Get score color
  const getScoreColor = (score) => {
    if (score >= 9) return '#10b981';
    if (score >= 7) return '#3b82f6';
    if (score >= 5) return '#f59e0b';
    return '#ef4444';
  };

  const scoreColor = decision.score ? getScoreColor(decision.score) : '#6b7280';

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
    <div className={`decision-item ${isExpanded ? 'expanded' : ''}`}>
      <div className="decision-item-main" onClick={onToggle}>
        {/* Correctness indicator */}
        <div
          className="decision-correctness"
          style={{
            color: display.color,
            backgroundColor: display.bgColor
          }}
        >
          {display.icon}
        </div>

        {/* Bid display */}
        <div className="decision-bid">
          <div className="bid-text">{bidDisplay}</div>
          {decision.key_concept && (
            <div className="bid-concept">
              <TermHighlight text={decision.key_concept} />
            </div>
          )}
        </div>

        {/* Score */}
        <div className="decision-score" style={{ color: scoreColor }}>
          <div className="score-value">{scoreDisplay}</div>
          <div className="score-label">/10</div>
        </div>

        {/* Timestamp */}
        <div className="decision-time">
          {formatTimestamp(decision.timestamp)}
        </div>

        {/* Expand indicator */}
        <div className="decision-expand">
          {isExpanded ? '▼' : '▶'}
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="decision-item-details">
          {decision.helpful_hint && (
            <div className="decision-hint">
              <div className="hint-icon">💡</div>
              <div className="hint-text">
                <TermHighlight text={decision.helpful_hint} />
              </div>
            </div>
          )}

          <div className="decision-metadata">
            <div className="metadata-item">
              <span className="metadata-label">Position:</span>
              <span className="metadata-value">{decision.position}</span>
            </div>
            <div className="metadata-item">
              <span className="metadata-label">Bid #:</span>
              <span className="metadata-value">{decision.bid_number}</span>
            </div>
            {decision.impact && (
              <div className="metadata-item">
                <span className="metadata-label">Impact:</span>
                <span className={`metadata-value impact-${decision.impact}`}>
                  {decision.impact}
                </span>
              </div>
            )}
            {decision.error_category && (
              <div className="metadata-item">
                <span className="metadata-label">Category:</span>
                <span className="metadata-value">{decision.error_category.replace(/_/g, ' ')}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RecentDecisionsCard;
