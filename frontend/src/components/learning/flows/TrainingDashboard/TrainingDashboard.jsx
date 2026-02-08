/**
 * TrainingDashboard.jsx
 *
 * Training Dashboard (Flow 10) - Analytics page showing learning progress.
 * This is a read-only analytics page that does NOT emit FlowResult.
 *
 * Layout:
 * - Header with period toggle
 * - Summary cards (hands, streak, accuracy)
 * - Skill breakdown bars
 * - Suggested practice with Start button
 * - Convention mastery chips
 * - Recent activity list
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { SkillBar, ProgressRing, StreakCalendar, PrimaryButton } from '../../shared';
import { getPerformanceLevel } from '../../types/flow-types';
import {
  calculateDashboardData,
  TIME_PERIODS,
  getFlowTypeName,
} from './TrainingDashboard.logic';
import './TrainingDashboard.css';

/**
 * TrainingDashboard - Main dashboard component
 *
 * @param {Object} props
 * @param {function} [props.onStartSuggested] - Callback when user clicks Start on a suggestion
 *   Called with (flowType: string, categories: string[])
 * @param {function} [props.onClose] - Callback to close the dashboard
 */
const TrainingDashboard = ({ onStartSuggested = null, onClose = null }) => {
  const [period, setPeriod] = useState(TIME_PERIODS.WEEK);
  const [data, setData] = useState(null);

  // Load dashboard data when period changes
  useEffect(() => {
    const dashboardData = calculateDashboardData(period);
    setData(dashboardData);
  }, [period]);

  const handlePeriodChange = useCallback((newPeriod) => {
    setPeriod(newPeriod);
  }, []);

  const handleStartSuggested = useCallback((recommendation) => {
    if (onStartSuggested) {
      const categories = [recommendation.category];
      if (recommendation.conventionTag) {
        categories.push(recommendation.conventionTag);
      }
      onStartSuggested(recommendation.flowType, categories);
    }
  }, [onStartSuggested]);

  // Format relative time for activity items
  const formatRelativeTime = useCallback((timestamp) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }, []);

  if (!data) {
    return (
      <div className="training-dashboard-overlay">
        <div className="training-dashboard">
          <div className="empty-state">
            <div className="empty-state-icon">Loading...</div>
          </div>
        </div>
      </div>
    );
  }

  const { summary, skillStats, conventionStats, recommendations, recentActivity, streakCalendar } = data;

  return (
    <div className="training-dashboard-overlay">
      <div className="training-dashboard">
        {/* Header */}
        <div className="dashboard-header">
          <h1 className="dashboard-title">Training Dashboard</h1>
          <div className="period-toggle">
          <button
            className={`period-btn ${period === TIME_PERIODS.WEEK ? 'active' : ''}`}
            onClick={() => handlePeriodChange(TIME_PERIODS.WEEK)}
          >
            Last 7 days
          </button>
          <button
            className={`period-btn ${period === TIME_PERIODS.MONTH ? 'active' : ''}`}
            onClick={() => handlePeriodChange(TIME_PERIODS.MONTH)}
          >
            Last 30 days
          </button>
          <button
            className={`period-btn ${period === TIME_PERIODS.ALL ? 'active' : ''}`}
            onClick={() => handlePeriodChange(TIME_PERIODS.ALL)}
          >
            All time
          </button>
        </div>
        {onClose && (
          <button
            className="dashboard-close-btn"
            onClick={onClose}
            aria-label="Close dashboard"
            type="button"
          >
            ✕
          </button>
        )}
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="stat-card">
          <span className="stat-label">Hands Played</span>
          <span className="stat-value">{summary.handsPlayed}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Streak</span>
          <span className="stat-value">
            {summary.streak}
            {summary.streak > 0 && (
              <span className="fire" role="img" aria-label="fire">{' '}&#128293;</span>
            )}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Accuracy</span>
          <span className="stat-value">{summary.accuracy}%</span>
          {summary.accuracyDiff !== 0 && (
            <span className={`stat-trend ${summary.accuracyTrend}`}>
              {summary.accuracyDiff > 0 ? '\u2191' : '\u2193'}{Math.abs(summary.accuracyDiff)}%
            </span>
          )}
        </div>
      </div>

      {/* Streak Calendar */}
      {streakCalendar && streakCalendar.length > 0 && (
        <div className="dashboard-section">
          <h2 className="section-title">
            <span className="section-icon" role="img" aria-label="calendar">&#128197;</span>
            Weekly Practice
          </h2>
          <div className="streak-section">
            <StreakCalendar days={streakCalendar} />
          </div>
        </div>
      )}

      {/* Skill Breakdown */}
      <div className="dashboard-section">
        <h2 className="section-title">
          <span className="section-icon" role="img" aria-label="chart">&#128202;</span>
          Skill Breakdown
        </h2>
        {skillStats.length > 0 ? (
          <div className="skill-breakdown">
            {skillStats.map((skill) => (
              <SkillBar
                key={skill.category}
                name={skill.name}
                percentage={skill.accuracy}
                showLabel
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state-text">
              Complete some training flows to see your skill breakdown.
            </div>
          </div>
        )}
      </div>

      {/* Suggested Practice */}
      <div className="dashboard-section suggestion-box">
        <h2 className="section-title">
          <span className="section-icon" role="img" aria-label="lightbulb">&#128161;</span>
          Suggested Practice
        </h2>
        {recommendations.length > 0 ? (
          recommendations.map((rec, index) => (
            <div key={rec.category} className="suggestion-content" style={index > 0 ? { marginTop: '12px' } : {}}>
              <div className="suggestion-text">
                <p>
                  <span className="highlight">{rec.name}</span>: {rec.description}
                </p>
              </div>
              <div className="suggestion-action">
                <PrimaryButton onClick={() => handleStartSuggested(rec)}>
                  Start &#8594;
                </PrimaryButton>
              </div>
            </div>
          ))
        ) : (
          <div className="suggestion-empty">
            Practice more to get personalized recommendations!
          </div>
        )}
      </div>

      {/* Convention Mastery */}
      {conventionStats.length > 0 && (
        <div className="dashboard-section">
          <h2 className="section-title">
            <span className="section-icon" role="img" aria-label="star">&#11088;</span>
            Convention Mastery
          </h2>
          <div className="convention-list">
            {conventionStats.map((conv) => (
              <div key={conv.tag} className="convention-chip">
                <span className="convention-name">{conv.name}</span>
                <span className={`convention-pct ${getPerformanceLevel(conv.accuracy)}`}>
                  {conv.accuracy}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="dashboard-section">
        <h2 className="section-title">
          <span className="section-icon" role="img" aria-label="clock">&#9200;</span>
          Recent Activity
        </h2>
        {recentActivity.length > 0 ? (
          <div className="activity-list">
            {recentActivity.map((activity, index) => (
              <div key={index} className="activity-item">
                <div className="activity-left">
                  <span className="activity-type">{getFlowTypeName(activity.flowType)}</span>
                  <span className="activity-time">{formatRelativeTime(activity.timestamp)}</span>
                </div>
                <div className="activity-right">
                  <span className={`activity-score ${getPerformanceLevel(activity.score)}`}>
                    {Math.round(activity.score)}%
                  </span>
                  <span className="activity-detail">
                    {activity.correctCount}/{activity.decisionsCount}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon" role="img" aria-label="empty">&#128237;</div>
            <div className="empty-state-text">
              No activity yet. Start practicing to see your history!
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  );
};

TrainingDashboard.propTypes = {
  onStartSuggested: PropTypes.func,
  onClose: PropTypes.func,
};

export default TrainingDashboard;
