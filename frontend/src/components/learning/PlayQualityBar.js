/**
 * PlayQualityBar Component - Play Feedback System
 *
 * Displays aggregate play quality statistics:
 * - Average quality score (0-10)
 * - Optimal play percentage
 * - Blunder rate
 * - Trend indicator (improving/stable/declining)
 *
 * Mirrors BiddingQualityBar structure for consistency
 */

import React from 'react';
import './PlayQualityBar.css';

const PlayQualityBar = ({ stats }) => {
  // Handle missing or empty stats
  if (!stats || stats.total_decisions === 0) {
    return (
      <div className="play-quality-bar empty-state">
        <div className="empty-state-content">
          <div className="empty-state-icon">🃏</div>
          <div className="empty-state-text">
            <p className="empty-state-title">No play data yet</p>
            <p className="empty-state-subtitle">
              Play through hands to see your card play quality stats
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Calculate percentages
  const optimalPercentage = Math.round(stats.optimal_rate * 100);
  const goodPercentage = Math.round(stats.good_rate * 100);
  const blunderPercentage = Math.round(stats.blunder_rate * 100);

  // Determine quality rating based on average score
  const getQualityRating = (score) => {
    if (score >= 9) return { label: 'Excellent', color: '#10b981' };
    if (score >= 8) return { label: 'Very Good', color: '#3b82f6' };
    if (score >= 7) return { label: 'Good', color: '#6366f1' };
    if (score >= 6) return { label: 'Fair', color: '#f59e0b' };
    if (score >= 5) return { label: 'Needs Work', color: '#ef4444' };
    return { label: 'Learning', color: '#9ca3af' };
  };

  const qualityRating = getQualityRating(stats.avg_score);

  // Trend emoji and label
  const getTrendDisplay = (trend) => {
    switch (trend) {
      case 'improving':
        return { emoji: '📈', label: 'Improving', color: '#10b981' };
      case 'declining':
        return { emoji: '📉', label: 'Declining', color: '#ef4444' };
      default:
        return { emoji: '➡️', label: 'Stable', color: '#6b7280' };
    }
  };

  const trendDisplay = getTrendDisplay(stats.recent_trend);

  return (
    <div className="play-quality-bar">
      {/* Average Score */}
      <div className="quality-stat-item quality-score">
        <div className="quality-score-circle" style={{ borderColor: qualityRating.color }}>
          <div className="quality-score-value">{stats.avg_score.toFixed(1)}</div>
          <div className="quality-score-max">/10</div>
        </div>
        <div className="quality-stat-label">
          <div className="quality-rating" style={{ color: qualityRating.color }}>
            {qualityRating.label}
          </div>
          <div className="quality-sublabel">Play Quality</div>
        </div>
      </div>

      {/* Optimal Plays */}
      <div className="quality-stat-item">
        <div className="quality-stat-value">
          {optimalPercentage}%
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label">Optimal Plays</div>
          <div className="quality-sublabel">
            {stats.optimal_rate > 0
              ? `${Math.round(stats.optimal_rate * stats.total_decisions)} of ${stats.total_decisions}`
              : 'None yet'}
          </div>
        </div>
        <div className="quality-progress-bar">
          <div
            className="quality-progress-fill optimal-fill"
            style={{ width: `${optimalPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Good Plays */}
      <div className="quality-stat-item">
        <div className="quality-stat-value">
          {goodPercentage}%
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label">Good Plays</div>
          <div className="quality-sublabel">
            {stats.good_rate > 0
              ? `${Math.round(stats.good_rate * stats.total_decisions)} of ${stats.total_decisions}`
              : 'None'}
          </div>
        </div>
        <div className="quality-progress-bar">
          <div
            className="quality-progress-fill good-fill"
            style={{ width: `${goodPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Blunder Rate */}
      <div className="quality-stat-item">
        <div className="quality-stat-value blunder-value">
          {blunderPercentage}%
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label">Blunders</div>
          <div className="quality-sublabel">
            {blunderPercentage > 0
              ? `${Math.round(stats.blunder_rate * stats.total_decisions)} plays`
              : 'None!'}
          </div>
        </div>
        <div className="quality-progress-bar">
          <div
            className="quality-progress-fill blunder-fill"
            style={{ width: `${blunderPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Trend */}
      <div className="quality-stat-item quality-trend">
        <div className="trend-icon" style={{ color: trendDisplay.color }}>
          {trendDisplay.emoji}
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label" style={{ color: trendDisplay.color }}>
            {trendDisplay.label}
          </div>
          <div className="quality-sublabel">Recent Trend</div>
        </div>
      </div>

      {/* Total Decisions Count */}
      <div className="quality-stat-item quality-count">
        <div className="quality-stat-value">
          {stats.total_decisions}
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label">Card Plays</div>
          <div className="quality-sublabel">Last 30 days</div>
        </div>
      </div>
    </div>
  );
};

export default PlayQualityBar;
