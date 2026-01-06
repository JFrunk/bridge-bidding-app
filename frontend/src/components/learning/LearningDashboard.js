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
import BidReviewModal from './BidReviewModal';
import ACBLImportModal from './ACBLImportModal';

const LearningDashboard = ({ userId, onStartLearning, onStartFreeplay }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedHandId, setSelectedHandId] = useState(null);
  const [reviewType, setReviewType] = useState(null); // 'play' or 'bidding'
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  // Track hand list for prev/next navigation in modals
  const [handListForNav, setHandListForNav] = useState([]);
  const [currentHandIndex, setCurrentHandIndex] = useState(-1);

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
  // Second parameter specifies type: 'play' (default) or 'bidding'
  // Third parameter is optional hand list for prev/next navigation
  const handleOpenReview = (handOrId, type = 'play', handList = []) => {
    const handId = typeof handOrId === 'object' ? handOrId.id : handOrId;
    if (handId) {
      setSelectedHandId(handId);
      setReviewType(type);
      setShowReviewModal(true);
      // Store hand list for navigation
      if (handList.length > 0) {
        setHandListForNav(handList);
        const idx = handList.findIndex(h => (h.id || h.hand_id) === handId);
        setCurrentHandIndex(idx >= 0 ? idx : 0);
      }
    }
  };

  // Navigate to previous/next hand in the list
  const handleNavigateHand = (direction) => {
    if (handListForNav.length === 0) return;
    const newIndex = currentHandIndex + direction;
    if (newIndex >= 0 && newIndex < handListForNav.length) {
      setCurrentHandIndex(newIndex);
      const hand = handListForNav[newIndex];
      setSelectedHandId(hand.id || hand.hand_id);
    }
  };

  // Handle closing hand review modal
  const handleCloseReview = () => {
    setShowReviewModal(false);
    setSelectedHandId(null);
    setReviewType(null);
    setHandListForNav([]);
    setCurrentHandIndex(-1);
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
        <div className="header-title-row">
          <div>
            <h2>Your Learning Journey</h2>
            <p className="learning-dashboard-subtitle">
              Track your progress and discover growth opportunities
            </p>
          </div>
          <button
            className="import-button"
            onClick={() => setShowImportModal(true)}
            title="Import tournament hands (PBN/BWS)"
          >
            Import Hands
          </button>
        </div>
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

      {/* Hand Review Modal - Play-by-play analysis */}
      {showReviewModal && selectedHandId && reviewType === 'play' && (
        <HandReviewModal
          handId={selectedHandId}
          onClose={handleCloseReview}
          // Navigation props
          onPrevHand={currentHandIndex > 0 ? () => handleNavigateHand(-1) : null}
          onNextHand={currentHandIndex < handListForNav.length - 1 ? () => handleNavigateHand(1) : null}
          currentIndex={currentHandIndex}
          totalHands={handListForNav.length}
        />
      )}

      {/* Bid Review Modal - Bid-by-bid analysis */}
      {showReviewModal && selectedHandId && reviewType === 'bidding' && (
        <BidReviewModal
          handId={selectedHandId}
          onClose={handleCloseReview}
          // Navigation props
          onPrevHand={currentHandIndex > 0 ? () => handleNavigateHand(-1) : null}
          onNextHand={currentHandIndex < handListForNav.length - 1 ? () => handleNavigateHand(1) : null}
          currentIndex={currentHandIndex}
          totalHands={handListForNav.length}
        />
      )}

      {/* ACBL Import Modal - Import PBN/BWS tournament files */}
      {showImportModal && (
        <ACBLImportModal
          isOpen={showImportModal}
          onClose={() => setShowImportModal(false)}
          userId={userId}
          onHandSelect={(hand) => {
            setShowImportModal(false);
            handleOpenReview(hand.id, 'play');
          }}
        />
      )}
    </div>
  );
};

export default LearningDashboard;
