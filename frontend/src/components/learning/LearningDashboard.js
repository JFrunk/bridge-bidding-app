/**
 * Learning Dashboard Component
 *
 * Displays the five-bar progress interface:
 * - Learn Bid, Practice Bid, Learn Play, Practice Play, Performance Overview
 * All content is consolidated into expandable horizontal bars.
 */

import React, { useState, useEffect, useCallback } from 'react';
import './LearningDashboard.css';
import { getDashboardData } from '../../services/analyticsService';
import FourDimensionProgress from './FourDimensionProgress';
import HandReviewModal from './HandReviewModal';

const LearningDashboard = ({ userId, onStartLearning, onStartFreeplay }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedHandId, setSelectedHandId] = useState(null);
  const [showReviewModal, setShowReviewModal] = useState(false);

  const loadDashboardData = useCallback(async () => {
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
  }, [userId]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Handle opening hand review modal
  // Accepts either a hand object with id property, or just the hand ID directly
  const handleOpenReview = (handOrId) => {
    const handId = typeof handOrId === 'object' ? handOrId.id : handOrId;
    if (handId) {
      setSelectedHandId(handId);
      setShowReviewModal(true);
    }
  };

  // Handle closing hand review modal
  const handleCloseReview = () => {
    setShowReviewModal(false);
    setSelectedHandId(null);
  };

  if (loading) {
    return (
      <div className="loading-dashboard" data-testid="dashboard-loading">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-dashboard" data-testid="dashboard-error">
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

  const { gameplay_stats, bidding_feedback_stats, play_feedback_stats, recent_decisions } = dashboardData;

  // Check if user has any meaningful data (for showing welcome message)
  const hasGameplayData = gameplay_stats && gameplay_stats.total_hands_played > 0;
  const hasBiddingData = bidding_feedback_stats && bidding_feedback_stats.total_decisions > 0;
  const hasPlayFeedbackData = play_feedback_stats && play_feedback_stats.total_decisions > 0;
  const hasAnyData = hasGameplayData || hasBiddingData || hasPlayFeedbackData || (recent_decisions && recent_decisions.length > 0);

  return (
    <div className="learning-dashboard" data-testid="dashboard-content">
      {/* Header */}
      <div className="learning-dashboard-header" data-testid="dashboard-header">
        <h2>Your Learning Journey</h2>
        <p className="learning-dashboard-subtitle">
          Track your progress and discover growth opportunities
        </p>
      </div>

      {/* Five-Bar Progress Section */}
      <div className="four-dimension-section">
        <FourDimensionProgress
          userId={userId}
          onStartLearning={onStartLearning}
          onStartPractice={onStartFreeplay}
          onReviewHand={handleOpenReview}
        />
      </div>

      {/* Welcome message for new players - shown when no data exists */}
      {!hasAnyData && (
        <div className="empty-dashboard-state" data-testid="dashboard-empty-state">
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

      {/* Hand Review Modal */}
      {showReviewModal && selectedHandId && (
        <HandReviewModal
          handId={selectedHandId}
          onClose={handleCloseReview}
        />
      )}
    </div>
  );
};

export default LearningDashboard;
