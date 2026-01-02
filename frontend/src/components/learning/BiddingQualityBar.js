/**
 * BiddingQualityBar Component - Phase 1: Bidding Feedback
 *
 * Displays aggregate bidding quality statistics:
 * - Average quality score (0-10)
 * - Optimal bid percentage
 * - Error rate
 * - Trend indicator (improving/stable/declining)
 *
 * Designed to match the existing stats bar styling in LearningDashboard
 */

import React from 'react';
import './BiddingQualityBar.css';

const BiddingQualityBar = ({ stats }) => {
  // Handle missing or empty stats
  if (!stats || stats.total_decisions === 0) {
    return (
      <div className="bidding-quality-bar empty-state">
        <div className="empty-state-content">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-text">
            <p className="empty-state-title">No bidding data yet</p>
            <p className="empty-state-subtitle">
              Make some bids during gameplay to see your quality stats
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Calculate percentages - using 3-tier system
  const optimalPercentage = Math.round(stats.optimal_rate * 100);
  const acceptablePercentage = Math.round(stats.acceptable_rate * 100);
  const goodPercentage = Math.round((stats.good_rate || (stats.optimal_rate + stats.acceptable_rate)) * 100);
  const suboptimalPercentage = Math.round((stats.suboptimal_rate || 0) * 100);
  const errorPercentage = Math.round(stats.error_rate * 100);

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
    <div className="bidding-quality-bar">
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
          <div className="quality-sublabel">Average Quality</div>
        </div>
      </div>

      {/* Good Bids (Optimal + Acceptable) */}
      <div className="quality-stat-item">
        <div className="quality-stat-value">
          {goodPercentage}%
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label">Good Bids</div>
          <div className="quality-sublabel">{optimalPercentage}% optimal, {acceptablePercentage}% acceptable</div>
        </div>
        <div className="quality-progress-bar stacked">
          <div
            className="quality-progress-fill optimal-fill"
            style={{ width: `${optimalPercentage}%` }}
          ></div>
          <div
            className="quality-progress-fill acceptable-fill"
            style={{ width: `${acceptablePercentage}%`, left: `${optimalPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Needs Work (Suboptimal) */}
      <div className="quality-stat-item">
        <div className="quality-stat-value suboptimal-value">
          {suboptimalPercentage}%
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label">Needs Work</div>
          <div className="quality-sublabel">Suboptimal bids</div>
        </div>
        <div className="quality-progress-bar">
          <div
            className="quality-progress-fill suboptimal-fill"
            style={{ width: `${suboptimalPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Errors */}
      <div className="quality-stat-item">
        <div className="quality-stat-value error-value">
          {errorPercentage}%
        </div>
        <div className="quality-stat-label">
          <div className="quality-main-label">Errors</div>
          <div className="quality-sublabel">
            {stats.critical_errors > 0 ? `${stats.critical_errors} critical` : 'No critical'}
          </div>
        </div>
        <div className="quality-progress-bar">
          <div
            className="quality-progress-fill error-fill"
            style={{ width: `${errorPercentage}%` }}
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
          <div className="quality-main-label">Decisions</div>
          <div className="quality-sublabel">Last 30 days</div>
        </div>
      </div>
    </div>
  );
};

export default BiddingQualityBar;
