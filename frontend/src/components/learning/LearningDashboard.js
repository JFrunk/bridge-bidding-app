/**
 * Learning Dashboard Component
 *
 * Displays comprehensive learning insights including:
 * - User stats (XP, level, streak, accuracy)
 * - Pending celebrations
 * - Growth opportunities (areas to improve)
 * - Recent wins (mastered patterns)
 * - Practice recommendations
 */

import React, { useState, useEffect } from 'react';
import './LearningDashboard.css';
import {
  getDashboardData,
  acknowledgeCelebration,
} from '../../services/analyticsService';
import BiddingQualityBar from './BiddingQualityBar';
import RecentDecisionsCard from './RecentDecisionsCard';

const LearningDashboard = ({ userId, onPracticeClick }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [userId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDashboardData(userId);
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledgeCelebration = async (milestoneId) => {
    try {
      await acknowledgeCelebration(milestoneId);
      // Refresh dashboard to remove acknowledged celebration
      loadDashboardData();
    } catch (err) {
      console.error('Failed to acknowledge celebration:', err);
    }
  };

  const handlePracticeNow = (recommendation) => {
    if (onPracticeClick) {
      onPracticeClick({
        conventionId: recommendation.convention_id,
        category: recommendation.error_category,
        recommendedHands: recommendation.recommended_hands,
      });
    }
  };

  if (loading) {
    return (
      <div className="loading-dashboard">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-dashboard">
        <div className="error-icon">⚠️</div>
        <h3 className="error-message">Failed to load dashboard: {error}</h3>
        <button className="retry-button" onClick={loadDashboardData}>
          Retry
        </button>
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  const { user_stats, gameplay_stats, bidding_feedback_stats, recent_decisions, insights, pending_celebrations, practice_recommendations } = dashboardData;

  // Check if user has any meaningful data
  const hasGameplayData = gameplay_stats && gameplay_stats.total_hands_played > 0;
  const hasBiddingData = bidding_feedback_stats && bidding_feedback_stats.total_decisions > 0;
  const hasAnyData = hasGameplayData || hasBiddingData || (recent_decisions && recent_decisions.length > 0);

  return (
    <div className="learning-dashboard">
      {/* Header */}
      <div className="learning-dashboard-header">
        <h2>Your Learning Journey</h2>
        <p className="learning-dashboard-subtitle">
          Track your progress and discover growth opportunities
        </p>
      </div>

      {/* Show welcome message for new players */}
      {!hasAnyData && (
        <div className="empty-dashboard-state">
          <div className="empty-dashboard-icon">🎯</div>
          <h3 className="empty-dashboard-title">Welcome to Bridge Learning!</h3>
          <p className="empty-dashboard-message">
            Start playing hands to see your progress here. Your stats, achievements, and personalized recommendations will appear as you practice.
          </p>
          <div className="empty-dashboard-tips">
            <p className="tip-title">💡 Tips to get started:</p>
            <ul className="tip-list">
              <li>Complete the bidding phase to track your bidding decisions</li>
              <li>Play through hands as declarer to build your gameplay stats</li>
              <li>Your dashboard will update automatically after each hand</li>
            </ul>
          </div>
        </div>
      )}

      {/* Bidding Stats Bar - only show if has data */}
      {user_stats && hasBiddingData && (
        <div className="stats-section">
          <h3 className="stats-section-title">Bidding</h3>
          <BiddingStatsBar stats={user_stats} />
        </div>
      )}

      {/* Gameplay Stats Bar - only show if has data */}
      {gameplay_stats && hasGameplayData && (
        <div className="stats-section">
          <h3 className="stats-section-title">Gameplay</h3>
          <GameplayStatsBar stats={gameplay_stats} />
        </div>
      )}

      {/* Bidding Quality Bar (Phase 1: NEW) - only show if has data */}
      {bidding_feedback_stats && hasBiddingData && (
        <div className="stats-section">
          <h3 className="stats-section-title">Bidding Quality</h3>
          <BiddingQualityBar stats={bidding_feedback_stats} />
        </div>
      )}

      {/* Dashboard Grid */}
      <div className="dashboard-grid">
        {/* Pending Celebrations */}
        {pending_celebrations && pending_celebrations.length > 0 && (
          <CelebrationsCard
            celebrations={pending_celebrations}
            onAcknowledge={handleAcknowledgeCelebration}
          />
        )}

        {/* Recent Bidding Decisions (Phase 1: NEW) */}
        {recent_decisions && recent_decisions.length > 0 && (
          <RecentDecisionsCard decisions={recent_decisions} />
        )}

        {/* Growth Opportunities */}
        {insights && insights.top_growth_areas && insights.top_growth_areas.length > 0 && (
          <GrowthAreasCard growthAreas={insights.top_growth_areas} />
        )}

        {/* Recent Wins */}
        {insights && insights.recent_wins && insights.recent_wins.length > 0 && (
          <RecentWinsCard recentWins={insights.recent_wins} />
        )}

        {/* Practice Recommendations */}
        {practice_recommendations && practice_recommendations.length > 0 && (
          <PracticeRecommendationsCard
            recommendations={practice_recommendations}
            onPracticeClick={handlePracticeNow}
          />
        )}

        {/* Overall Trend */}
        {insights && (
          <OverallTrendCard
            trend={insights.overall_trend}
            stats={{
              active: insights.active_patterns,
              improving: insights.improving_patterns,
              resolved: insights.resolved_patterns,
            }}
          />
        )}
      </div>
    </div>
  );
};

// Bidding Stats Bar Component
const BiddingStatsBar = ({ stats }) => {
  const xpProgress = stats.xp_to_next_level > 0
    ? ((stats.xp_to_next_level - (stats.xp_to_next_level - (stats.total_xp % stats.xp_to_next_level))) / stats.xp_to_next_level) * 100
    : 0;

  return (
    <div className="user-stats-bar">
      <div className="stat-item level-indicator">
        <div className="level-badge">Level {stats.current_level}</div>
        <div className="xp-progress">
          <div className="xp-progress-bar">
            <div className="xp-progress-fill" style={{ width: `${xpProgress}%` }}></div>
          </div>
          <div className="xp-text">
            {stats.total_xp} / {stats.xp_to_next_level} XP
          </div>
        </div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{stats.current_streak}</div>
        <div className="stat-label">Day Streak 🔥</div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{stats.total_hands}</div>
        <div className="stat-label">Hands Practiced</div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{Math.round(stats.overall_accuracy * 100)}%</div>
        <div className="stat-label">Overall Accuracy</div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{Math.round(stats.recent_accuracy * 100)}%</div>
        <div className="stat-label">Recent Accuracy</div>
      </div>
    </div>
  );
};

// Gameplay Stats Bar Component
const GameplayStatsBar = ({ stats }) => {
  return (
    <div className="user-stats-bar gameplay-stats-bar">
      <div className="stat-item">
        <div className="stat-value">{stats.total_hands_played}</div>
        <div className="stat-label">Hands Played</div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{stats.hands_as_declarer}</div>
        <div className="stat-label">As Declarer</div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{stats.contracts_made}</div>
        <div className="stat-label">Contracts Made</div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{Math.round(stats.declarer_success_rate * 100)}%</div>
        <div className="stat-label">Overall Success</div>
      </div>

      <div className="stat-item">
        <div className="stat-value">{Math.round(stats.recent_declarer_success_rate * 100)}%</div>
        <div className="stat-label">Recent Success</div>
      </div>
    </div>
  );
};

// Celebrations Card Component
const CelebrationsCard = ({ celebrations, onAcknowledge }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Celebrations 🎉</h3>
        <span className="dashboard-card-icon">✨</span>
      </div>
      <div className="dashboard-card-body">
        <div className="celebration-list">
          {celebrations.map((celebration) => (
            <div
              key={celebration.id}
              className="celebration-item"
              onClick={() => onAcknowledge(celebration.id)}
            >
              <div className="celebration-emoji">{celebration.emoji || '🎉'}</div>
              <div className="celebration-content">
                <h4 className="celebration-title">{celebration.title}</h4>
                <p className="celebration-message">{celebration.message}</p>
                <span className="celebration-xp">+{celebration.xp_reward} XP</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Growth Areas Card Component
const GrowthAreasCard = ({ growthAreas }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Growth Opportunities</h3>
        <span className="dashboard-card-icon">📈</span>
      </div>
      <div className="dashboard-card-body">
        {growthAreas.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">✅</div>
            <p className="empty-state-text">You're doing great! No areas need attention right now.</p>
          </div>
        ) : (
          <div className="growth-area-list">
            {growthAreas.map((area, index) => (
              <div
                key={index}
                className={`growth-area-item ${area.status}`}
              >
                <div className="growth-area-header">
                  <h4 className="growth-area-name">{area.category_name}</h4>
                  <span className={`growth-area-status status-${area.status.replace('_', '-')}`}>
                    {area.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="growth-area-stats">
                  <span className="growth-area-accuracy">
                    {Math.round(area.accuracy * 100)}% accurate
                  </span>
                  <span>•</span>
                  <span>{area.recent_occurrences} recent errors</span>
                  <span>•</span>
                  <span>{area.recommended_hands} hands recommended</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Recent Wins Card Component
const RecentWinsCard = ({ recentWins }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Recent Wins</h3>
        <span className="dashboard-card-icon">🏆</span>
      </div>
      <div className="dashboard-card-body">
        {recentWins.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🎯</div>
            <p className="empty-state-text">Keep practicing to see your wins here!</p>
          </div>
        ) : (
          <div className="recent-wins-list">
            {recentWins.map((win, index) => (
              <div key={index} className="recent-win-item">
                <div className="recent-win-header">
                  <h4 className="recent-win-name">{win.category_name}</h4>
                  <span className="recent-win-badge">
                    {win.status === 'resolved' ? 'Mastered!' : 'Improving!'}
                  </span>
                </div>
                <div className="recent-win-stats">
                  {Math.round(win.accuracy * 100)}% accurate
                  {win.improvement_rate > 0 && (
                    <span className="improvement-indicator">
                      +{Math.round(win.improvement_rate * 100)}% improvement
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Practice Recommendations Card Component
const PracticeRecommendationsCard = ({ recommendations, onPracticeClick }) => {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title">Recommended Practice</h3>
        <span className="dashboard-card-icon">🎯</span>
      </div>
      <div className="dashboard-card-body">
        {recommendations.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">✨</div>
            <p className="empty-state-text">All caught up! Great work!</p>
          </div>
        ) : (
          <div className="recommendation-list">
            {recommendations.map((rec, index) => (
              <div key={index} className="recommendation-item">
                <div className="recommendation-header">
                  <h4 className="recommendation-category">{rec.category_name}</h4>
                  <span className={`recommendation-priority priority-${rec.priority}`}>
                    Priority {rec.priority}
                  </span>
                </div>
                <p className="recommendation-reason">{rec.reason}</p>
                <div className="recommendation-action">
                  <span className="hands-count">
                    {rec.recommended_hands} hands recommended
                  </span>
                  <button
                    className="practice-button"
                    onClick={() => onPracticeClick(rec)}
                  >
                    Practice Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Overall Trend Card Component
const OverallTrendCard = ({ trend, stats }) => {
  const getTrendInfo = () => {
    switch (trend) {
      case 'improving':
        return {
          icon: '📈',
          text: 'You\'re Improving!',
          description: `${stats.improving} patterns getting better`,
          gradient: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
        };
      case 'mastering':
        return {
          icon: '🌟',
          text: 'You\'re Mastering It!',
          description: `${stats.resolved} patterns mastered`,
          gradient: 'linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%)',
        };
      case 'learning':
        return {
          icon: '📚',
          text: 'Keep Learning!',
          description: `${stats.active} active patterns to practice`,
          gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
        };
      case 'needs_attention':
        return {
          icon: '💪',
          text: 'Stay Focused!',
          description: 'Some areas need extra practice',
          gradient: 'linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%)',
        };
      default:
        return {
          icon: '🎯',
          text: 'Keep Going!',
          description: 'Practice makes perfect',
          gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
        };
    }
  };

  const trendInfo = getTrendInfo();

  return (
    <div className="dashboard-card">
      <div className="overall-trend" style={{ background: trendInfo.gradient }}>
        <div className="trend-icon">{trendInfo.icon}</div>
        <h3 className="trend-text">{trendInfo.text}</h3>
        <p className="trend-description">{trendInfo.description}</p>
      </div>
    </div>
  );
};

export default LearningDashboard;
