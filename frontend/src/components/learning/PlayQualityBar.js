/**
 * PlayQualityBar Component - DDS-Based Play Feedback
 *
 * Displays aggregate card play quality statistics:
 * - Overall play accuracy (0-10 score)
 * - Optimal play percentage
 * - Blunder rate
 * - Tricks lost to suboptimal play
 * - Category breakdown (expandable)
 * - Trend indicator (improving/stable/declining)
 *
 * Matches the BiddingQualityBar styling for visual consistency
 */

import React, { useState } from 'react';
import './PlayQualityBar.css';

const PlayQualityBar = ({ stats }) => {
  const [showCategories, setShowCategories] = useState(false);

  // Handle missing or empty stats
  if (!stats || stats.total_decisions === 0) {
    return (
      <div className="play-quality-bar empty-state">
        <div className="empty-state-content">
          <div className="empty-state-icon">🃏</div>
          <div className="empty-state-text">
            <p className="empty-state-title">No card play data yet</p>
            <p className="empty-state-subtitle">
              Play through hands to see your card play quality analysis
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Calculate percentages - using 3-tier system matching bidding
  const optimalPercentage = Math.round(stats.optimal_rate * 100);
  const goodPercentage = Math.round(stats.good_rate * 100);
  const combinedGoodPercentage = Math.round((stats.combined_good_rate || (stats.optimal_rate + stats.good_rate)) * 100);
  const suboptimalPercentage = Math.round((stats.suboptimal_rate || 0) * 100);
  const blunderPercentage = Math.round(stats.blunder_rate * 100);

  // Determine quality rating based on average score
  const getQualityRating = (score) => {
    if (score >= 9) return { label: 'Expert', color: '#10b981' };
    if (score >= 8) return { label: 'Strong', color: '#3b82f6' };
    if (score >= 7) return { label: 'Good', color: '#6366f1' };
    if (score >= 6) return { label: 'Developing', color: '#f59e0b' };
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

  // Get category breakdown
  const categories = stats.category_breakdown || {};
  const categoryList = Object.entries(categories)
    .sort((a, b) => b[1].attempts - a[1].attempts)
    .slice(0, 6); // Show top 6 categories

  // Get skill level styling
  const getSkillLevelStyle = (level) => {
    switch (level) {
      case 'strong':
        return { color: '#10b981', label: 'Strong' };
      case 'good':
        return { color: '#3b82f6', label: 'Good' };
      case 'developing':
        return { color: '#f59e0b', label: 'Developing' };
      case 'focus_area':
        return { color: '#ef4444', label: 'Focus Area' };
      default:
        return { color: '#9ca3af', label: 'Unknown' };
    }
  };

  return (
    <div className="play-quality-bar">
      {/* Main Stats Row */}
      <div className="play-quality-main">
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

        {/* Good Plays (Optimal + Good combined) */}
        <div className="quality-stat-item">
          <div className="quality-stat-value accuracy-value">
            {combinedGoodPercentage}%
          </div>
          <div className="quality-stat-label">
            <div className="quality-main-label">Good Plays</div>
            <div className="quality-sublabel">
              {optimalPercentage}% optimal, {goodPercentage}% good
            </div>
          </div>
          <div className="quality-progress-bar stacked">
            <div
              className="quality-progress-fill optimal-fill"
              style={{ width: `${optimalPercentage}%` }}
            ></div>
            <div
              className="quality-progress-fill good-fill"
              style={{ width: `${goodPercentage}%`, left: `${optimalPercentage}%` }}
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
            <div className="quality-sublabel">Suboptimal plays</div>
          </div>
          <div className="quality-progress-bar">
            <div
              className="quality-progress-fill suboptimal-fill"
              style={{ width: `${suboptimalPercentage}%` }}
            ></div>
          </div>
        </div>

        {/* Errors (Blunders) */}
        <div className="quality-stat-item">
          <div className="quality-stat-value blunder-value">
            {blunderPercentage}%
          </div>
          <div className="quality-stat-label">
            <div className="quality-main-label">Errors</div>
            <div className="quality-sublabel">
              {stats.total_tricks_lost || 0} tricks lost
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
            <div className="quality-main-label">Plays Analyzed</div>
            <div className="quality-sublabel">Last 30 days</div>
          </div>
        </div>
      </div>

      {/* Category Breakdown Toggle */}
      {categoryList.length > 0 && (
        <div className="category-breakdown-section">
          <button
            className="category-toggle-btn"
            onClick={() => setShowCategories(!showCategories)}
          >
            <span className="toggle-text">
              {showCategories ? 'Hide' : 'Show'} Category Breakdown
            </span>
            <span className={`toggle-arrow ${showCategories ? 'open' : ''}`}>▼</span>
          </button>

          {showCategories && (
            <div className="category-grid">
              {categoryList.map(([categoryId, catStats]) => {
                const skillStyle = getSkillLevelStyle(catStats.skill_level);
                return (
                  <div key={categoryId} className="category-card">
                    <div className="category-header">
                      <span className="category-name">{catStats.display_name}</span>
                      <span
                        className="category-skill-badge"
                        style={{ backgroundColor: skillStyle.color }}
                      >
                        {skillStyle.label}
                      </span>
                    </div>
                    <div className="category-stats">
                      <div className="category-stat">
                        <span className="category-stat-value">{catStats.accuracy}%</span>
                        <span className="category-stat-label">Accuracy</span>
                      </div>
                      <div className="category-stat">
                        <span className="category-stat-value">{catStats.attempts}</span>
                        <span className="category-stat-label">Plays</span>
                      </div>
                      <div className="category-stat">
                        <span className="category-stat-value">{catStats.avg_tricks_cost}</span>
                        <span className="category-stat-label">Avg Cost</span>
                      </div>
                    </div>
                    <div className="category-progress-bar">
                      <div
                        className="category-progress-fill"
                        style={{
                          width: `${catStats.accuracy}%`,
                          backgroundColor: skillStyle.color
                        }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PlayQualityBar;
