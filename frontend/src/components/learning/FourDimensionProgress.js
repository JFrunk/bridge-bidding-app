/**
 * Four-Dimension Progress Components (Redesigned)
 *
 * Layout: Horizontal expandable bars instead of 2x2 grid
 * Order: Learn Bid, Practice Bid, Learn Play, Practice Play, Performance Overview
 *
 * Features:
 * - Collapsed bars show: Icon + Title | Mini stats | Action button | Expand chevron
 * - Expanded content slides down with detailed information
 * - Visual segmented quality bars (Good/Needs Work/Errors)
 * - Play categories grid in Practice Play
 * - Performance quadrant chart in Overview section
 */

import React, { useState, useEffect } from 'react';
import { getFourDimensionProgress, getDashboardData, getHandHistory, getBoardAnalysis, getBiddingHandsHistory } from '../../services/analyticsService';
import ChartHelp from '../help/ChartHelp';
import './FourDimensionProgress.css';

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const FourDimensionProgress = ({
  userId,
  onStartLearning,
  onStartPractice,
  onShowHandHistory,
  onReviewHand
}) => {
  const [progressData, setProgressData] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [handHistory, setHandHistory] = useState([]);
  const [biddingHands, setBiddingHands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedBars, setExpandedBars] = useState({});

  useEffect(() => {
    loadAllData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all data in parallel
      const [progress, dashboard, history, biddingHistory] = await Promise.all([
        getFourDimensionProgress(userId),
        getDashboardData(userId).catch(() => null), // Dashboard data is optional
        getHandHistory(userId, 5).catch(() => ({ hands: [] })), // Hand history is optional
        getBiddingHandsHistory(userId, 5).catch(() => ({ hands: [] })) // Bidding hands history
      ]);

      setProgressData(progress);
      setDashboardData(dashboard);
      setHandHistory(history.hands || []);
      setBiddingHands(biddingHistory.hands || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleBar = (barId) => {
    setExpandedBars(prev => ({
      ...prev,
      [barId]: !prev[barId]
    }));
  };

  if (loading) {
    return (
      <div className="my-progress-loading">
        <div className="loading-spinner"></div>
        <p>Loading your progress...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="my-progress-error">
        <span className="error-icon">!</span>
        <p>Failed to load progress: {error}</p>
        <button onClick={loadAllData}>Retry</button>
      </div>
    );
  }

  if (!progressData) {
    return null;
  }

  const { bid_learning_journey, bid_practice_quality, play_learning_journey, play_practice_quality } = progressData;
  const userStats = dashboardData?.user_stats || {};

  return (
    <div className="my-progress">
      {/* Header with gamification */}
      <div className="my-progress-header">
        <h2>My Progress</h2>
        <div className="gamification-stats">
          {userStats.current_streak > 0 && (
            <span className="streak-badge">🔥 {userStats.current_streak} day streak</span>
          )}
          <span className="level-badge">⭐ Level {userStats.current_level || 1}</span>
          {userStats.total_xp > 0 && (
            <span className="xp-badge">{userStats.total_xp} XP</span>
          )}
        </div>
      </div>

      {/* Progress Bars Stack */}
      <div className="progress-bars-stack">
        {/* Learn Bid Bar */}
        <ProgressBar
          id="learn-bid"
          icon="📚"
          title="Learn Bid"
          miniStats={getLearnBidMiniStats(bid_learning_journey)}
          actionLabel="Continue →"
          onAction={() => onStartLearning?.('bidding')}
          expanded={expandedBars['learn-bid']}
          onToggle={() => toggleBar('learn-bid')}
          accentColor="primary"
        >
          <LearnBidExpanded
            journey={bid_learning_journey}
            conventions={bid_practice_quality.convention_mastery || []}
          />
        </ProgressBar>

        {/* Practice Bid Bar */}
        <ProgressBar
          id="practice-bid"
          icon="🎯"
          title="Practice Bid"
          miniStats={getPracticeBidMiniStats(bid_practice_quality, biddingHands.length)}
          actionLabel="Practice →"
          onAction={() => onStartPractice?.('bidding')}
          expanded={expandedBars['practice-bid']}
          onToggle={() => toggleBar('practice-bid')}
          accentColor="warning"
        >
          <PracticeBidExpanded
            quality={bid_practice_quality}
            biddingHands={biddingHands}
            onReviewHand={onReviewHand}
            onShowBiddingHistory={onShowHandHistory}
          />
        </ProgressBar>

        {/* Learn Play Bar */}
        <ProgressBar
          id="learn-play"
          icon="🃏"
          title="Learn Play"
          miniStats={getLearnPlayMiniStats(play_learning_journey)}
          actionLabel="Continue →"
          onAction={() => onStartLearning?.('play')}
          expanded={expandedBars['learn-play']}
          onToggle={() => toggleBar('learn-play')}
          accentColor="info"
        >
          <LearnPlayExpanded journey={play_learning_journey} />
        </ProgressBar>

        {/* Practice Play Bar */}
        <ProgressBar
          id="practice-play"
          icon="♠"
          title="Practice Play"
          miniStats={getPracticePlayMiniStats(play_practice_quality, handHistory.length)}
          actionLabel="Practice →"
          onAction={() => onStartPractice?.('play')}
          expanded={expandedBars['practice-play']}
          onToggle={() => toggleBar('practice-play')}
          accentColor="success"
        >
          <PracticePlayExpanded
            quality={play_practice_quality}
            handHistory={handHistory}
            onReviewHand={onReviewHand}
            onShowHandHistory={onShowHandHistory}
          />
        </ProgressBar>

        {/* Performance Overview Bar */}
        <ProgressBar
          id="performance-overview"
          icon="📊"
          title="Success Map"
          miniStats={getPerformanceOverviewMiniStats(bid_practice_quality, play_practice_quality)}
          expanded={expandedBars['performance-overview']}
          onToggle={() => toggleBar('performance-overview')}
          accentColor="neutral"
        >
          <BoardAnalysisExpanded
            userId={userId}
            onReviewHand={onReviewHand}
          />
        </ProgressBar>
      </div>
    </div>
  );
};

// ============================================================================
// MINI STATS HELPERS
// ============================================================================

const getLearnBidMiniStats = (journey) => {
  const level = journey?.current_level || 0;
  const skills = `${journey?.skills_completed_in_level || 0}/${journey?.skills_in_level || 0} skills`;
  const pct = Math.round(journey?.progress_percentage || 0);
  return `Level ${level} • ${skills} • ${pct}%`;
};

const getPracticeBidMiniStats = (quality, recentCount) => {
  const avg = Math.round(quality?.overall_accuracy || 0);
  const trend = quality?.recent_trend || 'stable';
  const trendIcon = trend === 'improving' ? '↗' : trend === 'declining' ? '↘' : '→';
  const totalHands = quality?.total_decisions || 0;
  // Show "X recent of Y total" when there are more hands than displayed
  const handsText = recentCount && recentCount < totalHands
    ? `${recentCount} of ${totalHands} hands`
    : `${totalHands} hands`;
  return `${avg}% avg • ${trendIcon} ${trend} • ${handsText}`;
};

const getLearnPlayMiniStats = (journey) => {
  const level = journey?.current_level || 0;
  const skills = `${journey?.skills_completed_in_level || 0}/${journey?.skills_in_level || 0} skills`;
  const pct = Math.round(journey?.progress_percentage || 0);
  return `Level ${level} • ${skills} • ${pct}%`;
};

const getPracticePlayMiniStats = (quality, recentCount) => {
  const playStats = quality?.play_decision_stats;
  const avg = Math.round(playStats?.optimal_rate || quality?.declarer_success_rate || 0);
  const trend = quality?.recent_trend || 'stable';
  const trendIcon = trend === 'improving' ? '↗' : trend === 'declining' ? '↘' : '→';
  const totalHands = quality?.total_hands_played || 0;
  // Show "X recent of Y total" when there are more hands than displayed
  const handsText = recentCount && recentCount < totalHands
    ? `${recentCount} of ${totalHands} hands`
    : `${totalHands} hands`;
  return `${avg}% quality • ${trendIcon} ${trend} • ${handsText}`;
};

const getPerformanceOverviewMiniStats = (bidQuality, playQuality) => {
  const bidPct = Math.round(bidQuality?.overall_accuracy || 0);
  const playPct = Math.round(playQuality?.play_decision_stats?.optimal_rate || playQuality?.declarer_success_rate || 0);

  // Determine quadrant message
  if (bidPct >= 70 && playPct >= 70) return "Strong overall!";
  if (bidPct >= 70) return "Good bidding, work on play";
  if (playPct >= 70) return "Good play, work on bidding";
  return "Room to improve both areas";
};

// ============================================================================
// PROGRESS BAR (Expandable Bar Component)
// ============================================================================

const ProgressBar = ({
  icon,
  title,
  miniStats,
  actionLabel,
  onAction,
  expanded,
  onToggle,
  accentColor,
  children
}) => {
  return (
    <div className={`expandable-progress-bar accent-${accentColor} ${expanded ? 'expanded' : ''}`}>
      {/* Collapsed Header */}
      <div className="expandable-progress-bar-header" onClick={onToggle}>
        <div className="bar-left">
          <span className="bar-icon">{icon}</span>
          <span className="bar-title">{title}</span>
        </div>
        <div className="bar-center">
          <span className="bar-mini-stats">{miniStats}</span>
        </div>
        <div className="bar-right">
          <span className={`bar-chevron ${expanded ? 'rotated' : ''}`}>▼</span>
        </div>
      </div>

      {/* Expanded Content */}
      <div className={`expandable-progress-bar-content ${expanded ? 'show' : ''}`}>
        {children}
        {/* Action button only visible when expanded */}
        {actionLabel && onAction && (
          <div className="bar-action-container">
            <button
              className="bar-action-btn-muted"
              onClick={(e) => {
                e.stopPropagation();
                onAction();
              }}
            >
              {actionLabel}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// LEARN BID EXPANDED
// ============================================================================

const LearnBidExpanded = ({ journey, conventions }) => {
  const {
    current_level,
    current_level_name,
    skills_in_level,
    skills_completed_in_level,
    total_skills_mastered,
    skills_in_progress,
    current_skill_progress,
    next_skill,
    level_progress
  } = journey || {};

  const levelPercentage = skills_in_level > 0
    ? Math.round((skills_completed_in_level / skills_in_level) * 100)
    : 0;

  // Filter conventions by level
  const essential = conventions.filter(c => c.level === 'essential');
  const intermediate = conventions.filter(c => c.level === 'intermediate');
  const showIntermediate = current_level >= 5;

  return (
    <div className="expanded-content learn-bid-content">
      {/* Current Level */}
      <div className="level-section">
        <div className="level-header">
          <div className="level-ring">
            <svg viewBox="0 0 100 100">
              <circle className="ring-bg" cx="50" cy="50" r="42" />
              <circle
                className="ring-fill"
                cx="50" cy="50" r="42"
                strokeDasharray={`${levelPercentage * 2.64} 264`}
                transform="rotate(-90 50 50)"
              />
              <text x="50" y="45" textAnchor="middle" className="ring-level">L{current_level}</text>
              <text x="50" y="62" textAnchor="middle" className="ring-progress">
                {skills_completed_in_level}/{skills_in_level}
              </text>
            </svg>
          </div>
          <div className="level-info">
            <div className="level-name">{current_level_name || `Level ${current_level}`}</div>
            <div className="level-detail">
              {total_skills_mastered > 0
                ? `${total_skills_mastered} skills mastered`
                : skills_in_progress > 0
                  ? `${skills_in_progress} skill${skills_in_progress > 1 ? 's' : ''} in progress`
                  : 'Ready to start!'}
            </div>
          </div>
        </div>

        {/* Level Roadmap */}
        <div className="level-roadmap">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((level) => {
            const levelId = level_progress ? Object.keys(level_progress).find(
              (id) => level_progress[id].level === level
            ) : null;
            const levelData = levelId ? level_progress[levelId] : null;

            let status = 'locked';
            if (levelData) {
              if (levelData.completed === levelData.total) {
                status = 'completed';
              } else if (levelData.unlocked) {
                status = level === current_level ? 'current' : 'unlocked';
              }
            }

            return (
              <div
                key={level}
                className={`roadmap-node ${status}`}
                title={levelData?.name || `Level ${level}`}
              >
                {status === 'completed' ? '✓' : level}
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Skill Progress */}
      {current_skill_progress && current_skill_progress.attempts > 0 && (
        <div className="current-skill-box">
          <div className="skill-header">
            <span className="skill-label">Current:</span>
            <span className="skill-name">{next_skill?.name || current_skill_progress.skill_id}</span>
          </div>
          <div className="skill-stats">
            <span>{current_skill_progress.attempts} attempts</span>
            <span>{current_skill_progress.accuracy}% accuracy</span>
          </div>
          <div className="skill-bar">
            <div className="skill-fill" style={{ width: `${Math.min(current_skill_progress.accuracy, 100)}%` }} />
          </div>
          <div className="skill-hint">
            {current_skill_progress.accuracy >= 80
              ? 'Almost mastered!'
              : `Need 80% accuracy to master`}
          </div>
        </div>
      )}

      {/* Next Skill */}
      {next_skill && (!current_skill_progress || current_skill_progress.attempts === 0) && (
        <div className="next-skill-box">
          <span className="next-label">Next:</span>
          <span className="next-name">{next_skill.name}</span>
        </div>
      )}

      {/* Conventions */}
      {conventions.length > 0 && (
        <div className="conventions-section">
          <div className="section-title">Conventions Unlocked</div>
          <div className="convention-chips">
            {essential.map(conv => (
              <ConventionChip key={conv.id} conv={conv} />
            ))}
            {showIntermediate && intermediate.map(conv => (
              <ConventionChip key={conv.id} conv={conv} />
            ))}
            {!showIntermediate && (
              <span className="locked-chip">🔒 More at Level 5</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const ConventionChip = ({ conv }) => {
  const statusIcon = conv.status === 'mastered' ? '✓' : conv.status === 'in_progress' ? '◐' : '○';
  const statusClass = conv.status === 'mastered' ? 'mastered' : conv.status === 'in_progress' ? 'in-progress' : 'not-started';

  return (
    <span className={`convention-chip ${statusClass}`}>
      <span className="chip-status">{statusIcon}</span>
      <span className="chip-name">{conv.name}</span>
      {conv.attempts > 0 && <span className="chip-accuracy">{conv.accuracy}%</span>}
    </span>
  );
};

// ============================================================================
// PRACTICE BID EXPANDED
// ============================================================================

const PracticeBidExpanded = ({ quality, biddingHands, onReviewHand, onShowBiddingHistory }) => {
  const [showAll, setShowAll] = useState(false);
  const goodRate = quality?.good_rate || 0;
  const suboptimalRate = quality?.suboptimal_rate || 0;
  const errorRate = quality?.error_rate || 0;
  const avgScore = Math.round(quality?.overall_accuracy || 0);

  // Show 4 hands initially, 10 when expanded
  const displayCount = showAll ? 10 : 4;
  const handsToShow = biddingHands?.slice(0, displayCount) || [];
  const hasMore = biddingHands && biddingHands.length > displayCount;
  const totalHands = quality?.total_decisions || 0;

  return (
    <div className="expanded-content practice-bid-content">
      {/* Quality Breakdown with Segmented Bar */}
      <div className="quality-section">
        <div className="quality-header">
          <span className="quality-value">{avgScore}%</span>
          <span className="quality-label">Bid Quality</span>
        </div>
        <SegmentedQualityBar
          good={goodRate}
          suboptimal={suboptimalRate}
          error={errorRate}
        />
      </div>

      {/* Recent Bidding Hands */}
      {biddingHands && biddingHands.length > 0 && (
        <div className="recent-hands-section">
          <div className="section-header">
            <span className="section-title">Recent Hands</span>
            {onShowBiddingHistory && totalHands > 10 && (
              <button className="see-all-btn" onClick={() => onShowBiddingHistory?.('bidding')}>
                See All {totalHands} →
              </button>
            )}
          </div>
          <div className="hands-list">
            {handsToShow.map((hand, idx) => (
              <BiddingHandRow
                key={hand.hand_id || idx}
                hand={hand}
                onReview={() => onReviewHand?.(hand.hand_id, 'bidding', biddingHands)}
              />
            ))}
          </div>
          {/* Show More / Show Less toggle */}
          {biddingHands.length > 4 && (
            <div className="show-more-container">
              <button
                className="show-more-btn"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? 'Show Less ↑' : `Show More (${Math.min(biddingHands.length, 10) - 4} more) ↓`}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Focus Areas */}
      {quality?.weakest_convention && (
        <div className="focus-areas-section">
          <div className="section-title">Focus Areas</div>
          <div className="focus-item">
            🎯 {quality.weakest_convention.name} - {quality.weakest_convention.accuracy}%
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// BIDDING HAND ROW - Shows hand summary with HCP, shape, contract, score
// ============================================================================

const BiddingHandRow = ({ hand, onReview }) => {
  const userHand = hand.user_hand || {};
  const hcp = userHand.hcp ?? '?';
  const shape = userHand.shape || '?-?-?-?';
  const features = userHand.features || [];
  const contract = hand.contract || 'Pass';
  const quality = hand.quality_pct || 0;
  const role = hand.role || 'Bidder';

  // Determine quality indicator
  const getQualityClass = (pct) => {
    if (pct >= 80) return 'good';
    if (pct >= 50) return 'suboptimal';
    return 'error';
  };

  // Get strain class for contract styling - uses standard red/black colors
  const getStrainClass = (contractStr) => {
    if (!contractStr) return '';
    if (contractStr.includes('♠') || contractStr.includes('S')) return 'spades';
    if (contractStr.includes('♥') || contractStr.includes('H')) return 'hearts';
    if (contractStr.includes('♦') || contractStr.includes('D')) return 'diamonds';
    if (contractStr.includes('♣') || contractStr.includes('C')) return 'clubs';
    if (contractStr.includes('NT') || contractStr.includes('N')) return 'notrump';
    return '';
  };

  // Order: Role, Final bid, HCP, Shape, Balanced (feature), Quality%, Review button
  return (
    <div className="bidding-hand-row">
      <span className="role">{role}</span>
      <span className={`contract ${getStrainClass(contract)}`}>{contract}</span>
      <span className="hcp-badge">{hcp} HCP</span>
      <span className="shape-badge">{shape}</span>
      {features.length > 0 && (
        <span className="feature-badge" title={features.join(', ')}>
          {features[0]}
        </span>
      )}
      <span className={`quality ${getQualityClass(quality)}`}>{quality}%</span>
      {onReview && (
        <button className="review-btn-primary" onClick={onReview}>Review</button>
      )}
    </div>
  );
};

// ============================================================================
// LEARN PLAY EXPANDED
// ============================================================================

const LearnPlayExpanded = ({ journey }) => {
  const {
    current_level,
    current_level_name,
    skills_in_level,
    skills_completed_in_level,
    total_skills_mastered,
    skills_in_progress,
    current_skill_progress,
    next_skill,
    level_progress
  } = journey || {};

  const levelPercentage = skills_in_level > 0
    ? Math.round((skills_completed_in_level / skills_in_level) * 100)
    : 0;

  return (
    <div className="expanded-content learn-play-content">
      {/* Current Level */}
      <div className="level-section">
        <div className="level-header">
          <div className="level-ring">
            <svg viewBox="0 0 100 100">
              <circle className="ring-bg" cx="50" cy="50" r="42" />
              <circle
                className="ring-fill ring-fill-play"
                cx="50" cy="50" r="42"
                strokeDasharray={`${levelPercentage * 2.64} 264`}
                transform="rotate(-90 50 50)"
              />
              <text x="50" y="45" textAnchor="middle" className="ring-level">L{current_level}</text>
              <text x="50" y="62" textAnchor="middle" className="ring-progress">
                {skills_completed_in_level}/{skills_in_level}
              </text>
            </svg>
          </div>
          <div className="level-info">
            <div className="level-name">{current_level_name || `Level ${current_level}`}</div>
            <div className="level-detail">
              {total_skills_mastered > 0
                ? `${total_skills_mastered} skills mastered`
                : skills_in_progress > 0
                  ? `${skills_in_progress} skill${skills_in_progress > 1 ? 's' : ''} in progress`
                  : 'Ready to start!'}
            </div>
          </div>
        </div>

        {/* Level Roadmap */}
        <div className="level-roadmap">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((level) => {
            const levelId = level_progress ? Object.keys(level_progress).find(
              (id) => level_progress[id].level === level
            ) : null;
            const levelData = levelId ? level_progress[levelId] : null;

            let status = 'locked';
            if (levelData) {
              if (levelData.completed === levelData.total) {
                status = 'completed';
              } else if (levelData.unlocked) {
                status = level === current_level ? 'current' : 'unlocked';
              }
            }

            return (
              <div
                key={level}
                className={`roadmap-node ${status}`}
                title={levelData?.name || `Level ${level}`}
              >
                {status === 'completed' ? '✓' : level}
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Skill Progress */}
      {current_skill_progress && current_skill_progress.attempts > 0 && (
        <div className="current-skill-box">
          <div className="skill-header">
            <span className="skill-label">Current:</span>
            <span className="skill-name">{next_skill?.name || current_skill_progress.skill_id}</span>
          </div>
          <div className="skill-stats">
            <span>{current_skill_progress.attempts} attempts</span>
            <span>{current_skill_progress.accuracy}% accuracy</span>
          </div>
          <div className="skill-bar skill-bar-play">
            <div className="skill-fill" style={{ width: `${Math.min(current_skill_progress.accuracy, 100)}%` }} />
          </div>
        </div>
      )}

      {/* Next Skill */}
      {next_skill && (!current_skill_progress || current_skill_progress.attempts === 0) && (
        <div className="next-skill-box">
          <span className="next-label">Next:</span>
          <span className="next-name">{next_skill.name}</span>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// PRACTICE PLAY EXPANDED
// ============================================================================

const PracticePlayExpanded = ({ quality, handHistory, onReviewHand, onShowHandHistory }) => {
  const [showAll, setShowAll] = useState(false);
  const playStats = quality?.play_decision_stats || {};
  const hasPlayData = playStats.optimal_rate > 0 || playStats.avg_score > 0;

  const goodRate = hasPlayData ? (playStats.good_rate || 0) : 0;
  const suboptimalRate = hasPlayData ? (playStats.suboptimal_rate || 0) : 0;
  const blunderRate = hasPlayData ? (playStats.blunder_rate || 0) : 0;
  const avgQuality = Math.round(hasPlayData ? playStats.optimal_rate : (quality?.declarer_success_rate || 0));

  // Category data now comes from play_decision_stats in the four-dimension progress API
  const tricksLost = playStats?.total_tricks_lost || 0;
  const totalHands = quality?.total_hands_played || 0;

  // Show 4 hands initially, 10 when expanded
  const displayCount = showAll ? 10 : 4;
  const handsToShow = handHistory?.slice(0, displayCount) || [];

  return (
    <div className="expanded-content practice-play-content">
      {/* Quality Breakdown with Segmented Bar */}
      <div className="quality-section">
        <div className="quality-header">
          <span className="quality-value">{avgQuality}%</span>
          <span className="quality-label">
            {hasPlayData ? 'Play Quality' : 'Success Rate'}
            {tricksLost > 0 && <span className="tricks-lost"> • {tricksLost} tricks lost</span>}
          </span>
        </div>
        {hasPlayData && (
          <SegmentedQualityBar
            good={goodRate}
            suboptimal={suboptimalRate}
            error={blunderRate}
            labels={{ good: 'Good', suboptimal: 'Suboptimal', error: 'Blunders' }}
          />
        )}
      </div>

      {/* Recent Hands */}
      {handHistory.length > 0 && (
        <div className="recent-hands-section">
          <div className="section-header">
            <span className="section-title">Recent Hands</span>
            {onShowHandHistory && totalHands > 10 && (
              <button className="see-all-btn" onClick={onShowHandHistory}>
                See All {totalHands} →
              </button>
            )}
          </div>
          <div className="hands-list">
            {handsToShow.map((hand, idx) => (
              <HandRow
                key={hand.id || idx}
                hand={hand}
                onReview={() => onReviewHand?.(hand.id, 'play', handHistory)}
              />
            ))}
          </div>
          {/* Show More / Show Less toggle */}
          {handHistory.length > 4 && (
            <div className="show-more-container">
              <button
                className="show-more-btn"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? 'Show Less ↑' : `Show More (${Math.min(handHistory.length, 10) - 4} more) ↓`}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// BOARD ANALYSIS EXPANDED - Redesigned Performance Chart
// ============================================================================
// Layout:
//   X-axis (horizontal): Card Play (Weak left, Good right)
//   Y-axis (vertical): Bidding (Weak bottom, Good top)
//
// Quadrants:
//   Top-Right: Good Bidding, Good Card Play (GREEN)
//   Top-Left: Good Bidding, Weak Card Play (YELLOW)
//   Bottom-Right: Weak Bidding, Good Card Play (YELLOW)
//   Bottom-Left: Weak Bidding, Weak Card Play (RED)
//
// Card Icons:
//   - Card-shaped rectangles (portrait orientation)
//   - Show contract inside (e.g., "4♠", "3NT")
//   - Color based on quadrant (green/yellow/red)
//   - Fill style based on user's role:
//     - Solid: User was declarer
//     - Hollow (thin border): Partner was declarer (user was dummy)
//     - Hollow (thick border): User was defending
// ============================================================================

// Helper to convert score from declarer's perspective to NS (user's) perspective
const getScoreForUser = (board) => {
  const declarerScore = board.actual_score || 0;
  const declarer = board.declarer;

  // If declarer is NS (N or S), score is already from user's perspective
  // If declarer is EW (E or W), negate the score to show user's perspective
  const isDeclarerNS = declarer === 'N' || declarer === 'S';
  return isDeclarerNS ? declarerScore : -declarerScore;
};

// Helper to format tricks display from user's perspective
const getTricksForUser = (board) => {
  const actualTricks = board.actual_tricks || 0;
  const contractLevel = parseInt(board.contract?.match(/\d/)?.[0] || '0', 10);
  const tricksNeeded = contractLevel + 6;

  if (board.user_was_defender) {
    // As defender: show how many you set them by, or how many they made over
    if (actualTricks < tricksNeeded) {
      return `Set ${tricksNeeded - actualTricks}`;
    } else {
      const over = actualTricks - tricksNeeded;
      return over > 0 ? `Made +${over}` : 'Made exactly';
    }
  } else {
    // As declarer/dummy: show your result
    if (board.made) {
      const over = actualTricks - tricksNeeded;
      return over > 0 ? `Made +${over}` : 'Made';
    } else {
      return `Down ${tricksNeeded - actualTricks}`;
    }
  }
};

const BoardAnalysisExpanded = ({ userId, onReviewHand }) => {
  const [boards, setBoards] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState(null);
  const [summary, setSummary] = useState({ total_boards: 0, good_good: 0, good_bad: 0, bad_good: 0, bad_bad: 0 });

  useEffect(() => {
    loadBoardAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, selectedSession]);

  const loadBoardAnalysis = async () => {
    if (!userId) return;

    try {
      setLoading(true);
      const data = await getBoardAnalysis(userId, selectedSession, 25);
      setBoards(data.boards || []);
      setSessions(data.sessions || []);
      setSummary(data.summary || { total_boards: 0, good_good: 0, good_bad: 0, bad_good: 0, bad_bad: 0 });
    } catch (err) {
      console.error('Failed to load board analysis:', err);
      setBoards([]);
    } finally {
      setLoading(false);
    }
  };

  // Group boards by quadrant based on NEW axis orientation
  // X-axis = Card Play (left=weak, right=good)
  // Y-axis = Bidding (bottom=weak, top=good)
  const quadrants = {
    'top-right': [],    // Good Bidding + Good Play (GREEN)
    'top-left': [],     // Good Bidding + Weak Play (YELLOW)
    'bottom-right': [], // Weak Bidding + Good Play (YELLOW)
    'bottom-left': []   // Weak Bidding + Weak Play (RED)
  };

  boards.forEach(board => {
    const playGood = board.play_quality === 'good';
    const bidGood = board.bidding_quality === 'good';

    if (bidGood && playGood) quadrants['top-right'].push(board);
    else if (bidGood && !playGood) quadrants['top-left'].push(board);
    else if (!bidGood && playGood) quadrants['bottom-right'].push(board);
    else quadrants['bottom-left'].push(board);
  });

  // Color logic based on quadrant
  const getQuadrantColor = (quadrantKey) => {
    switch (quadrantKey) {
      case 'top-right': return '#22c55e';   // Green - both good
      case 'top-left': return '#eab308';    // Yellow - good bid, weak play
      case 'bottom-right': return '#eab308'; // Yellow - weak bid, good play
      case 'bottom-left': return '#ef4444';  // Red - both weak
      default: return '#9ca3af';
    }
  };

  // Domain-specific colors for differential analysis
  // Used when board has diagnostic_domain from bidding feedback
  const getDomainColor = (domain) => {
    switch (domain) {
      case 'safety': return '#8b5cf6';     // Purple - LoTT/safety violations
      case 'value': return '#eab308';       // Yellow - Working HCP issues
      case 'control': return '#f97316';     // Orange - Trump control issues
      case 'tactical': return '#3b82f6';    // Blue - Tactical/preempt issues
      case 'defensive': return '#22c55e';   // Green - Defensive issues
      default: return null;
    }
  };

  // Get fill style based on user's role and optional domain coloring
  const getCardStyle = (board, quadrantKey) => {
    // Use domain color if available on error quadrants (bottom-left, top-left, bottom-right)
    const domainColor = board.diagnostic_domain ? getDomainColor(board.diagnostic_domain) : null;
    const usesDomainColor = domainColor && quadrantKey !== 'top-right'; // Don't override green "both good" cards

    const color = usesDomainColor ? domainColor : getQuadrantColor(quadrantKey);

    if (board.user_was_declarer) {
      // Solid fill - user declared
      return { fill: color, stroke: color, strokeWidth: 1 };
    } else if (board.user_was_dummy) {
      // Hollow with thin border - partner declared
      return { fill: 'white', stroke: color, strokeWidth: 1.5 };
    } else {
      // Hollow with thick border - defending
      return { fill: 'white', stroke: color, strokeWidth: 3 };
    }
  };

  // Grid packing: position cards in rows within each quadrant (4 per row, up to 20)
  const getGridPosition = (quadrantKey, index) => {
    const cols = 4;
    const row = Math.floor(index / cols);
    const col = index % cols;
    const cardWidth = 28;
    const cardHeight = 36;
    const spacingX = cardWidth + 4;
    const spacingY = cardHeight + 4;

    // Quadrant starting positions (top-left corner of each quadrant's card area)
    // Chart is 360x320, quadrants are roughly 175x155 each
    const startPositions = {
      'top-right': { x: 200, y: 35 },    // Right side, top
      'top-left': { x: 25, y: 35 },      // Left side, top
      'bottom-right': { x: 200, y: 195 }, // Right side, bottom
      'bottom-left': { x: 25, y: 195 }   // Left side, bottom
    };

    const start = startPositions[quadrantKey];
    return {
      x: start.x + col * spacingX,
      y: start.y + row * spacingY
    };
  };

  // Quadrant descriptions
  const quadrantDescriptions = {
    'top-right': 'Good Bidding, Good Card Play',
    'top-left': 'Good Bidding, Weak Card Play',
    'bottom-right': 'Weak Bidding, Good Card Play',
    'bottom-left': 'Weak Bidding, Weak Card Play'
  };

  const handleBoardClick = (handId) => {
    if (onReviewHand && handId) {
      onReviewHand(handId);
    }
  };

  const handleMouseEnter = (e, board) => {
    const rect = e.target.getBoundingClientRect();
    setTooltip({
      board,
      x: rect.left + rect.width / 2,
      y: rect.top - 10
    });
  };

  const handleMouseLeave = () => {
    setTooltip(null);
  };

  if (loading) {
    return (
      <div className="expanded-content board-analysis-content">
        <div className="board-analysis-loading">Loading board analysis...</div>
      </div>
    );
  }

  if (boards.length === 0) {
    return (
      <div className="expanded-content board-analysis-content">
        <div className="board-analysis-empty">
          <p>No analyzed boards yet.</p>
          <p className="empty-hint">Complete hands with DDS analysis enabled to see your performance breakdown.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="expanded-content board-analysis-content">
      {/* Header with Session Filter and Help */}
      <div className="board-analysis-header">
        <div className="session-filter">
          <select
            value={selectedSession || ''}
            onChange={e => setSelectedSession(e.target.value || null)}
            className="session-select"
          >
            <option value="">Last 25 hands</option>
            {sessions.map(s => (
              <option key={s.session_id} value={s.session_id}>
                Session ({s.hands_count} hands)
              </option>
            ))}
          </select>
        </div>
        <ChartHelp chartType="success-map" variant="icon" />
      </div>

      {/* Board Analysis Chart */}
      <div className="board-analysis-chart-container">
        <svg viewBox="0 0 360 340" className="board-analysis-chart">
          {/* Quadrant backgrounds */}
          <rect x="20" y="20" width="160" height="150" rx="8" fill="#fefce8" /> {/* Top-left: yellow bg */}
          <rect x="185" y="20" width="160" height="150" rx="8" fill="#dcfce7" /> {/* Top-right: green bg */}
          <rect x="20" y="175" width="160" height="150" rx="8" fill="#fee2e2" /> {/* Bottom-left: red bg */}
          <rect x="185" y="175" width="160" height="150" rx="8" fill="#fefce8" /> {/* Bottom-right: yellow bg */}

          {/* Quadrant divider lines */}
          <line x1="182" y1="20" x2="182" y2="325" stroke="#d1d5db" strokeWidth="1" strokeDasharray="4,4" />
          <line x1="20" y1="172" x2="345" y2="172" stroke="#d1d5db" strokeWidth="1" strokeDasharray="4,4" />

          {/* Quadrant description labels (centered at top of each quadrant) */}
          <text x="100" y="35" textAnchor="middle" className="chart-quadrant-desc">{quadrantDescriptions['top-left']}</text>
          <text x="265" y="35" textAnchor="middle" className="chart-quadrant-desc">{quadrantDescriptions['top-right']}</text>
          <text x="100" y="190" textAnchor="middle" className="chart-quadrant-desc">{quadrantDescriptions['bottom-left']}</text>
          <text x="265" y="190" textAnchor="middle" className="chart-quadrant-desc">{quadrantDescriptions['bottom-right']}</text>

          {/* X-axis: Card Play */}
          <text x="182" y="338" textAnchor="middle" className="chart-axis-label">Card Play</text>
          <text x="25" y="338" textAnchor="start" className="chart-axis-marker">Weak</text>
          <text x="340" y="338" textAnchor="end" className="chart-axis-marker">Good</text>

          {/* Y-axis: Bidding */}
          <text x="8" y="172" textAnchor="middle" transform="rotate(-90, 8, 172)" className="chart-axis-label">Bidding</text>
          <text x="8" y="320" textAnchor="middle" transform="rotate(-90, 8, 320)" className="chart-axis-marker">Weak</text>
          <text x="8" y="30" textAnchor="middle" transform="rotate(-90, 8, 30)" className="chart-axis-marker">Good</text>

          {/* Card icons for each quadrant */}
          {Object.entries(quadrants).map(([quadrantKey, quadrantBoards]) =>
            quadrantBoards.slice(0, 20).map((board, index) => {
              const pos = getGridPosition(quadrantKey, index);
              const style = getCardStyle(board, quadrantKey);
              const cardWidth = 28;
              const cardHeight = 36;

              return (
                <g
                  key={board.hand_id}
                  className="board-card"
                  onClick={() => handleBoardClick(board.hand_id)}
                  onMouseEnter={(e) => handleMouseEnter(e, board)}
                  onMouseLeave={handleMouseLeave}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Card-shaped rectangle (portrait orientation) */}
                  <rect
                    x={pos.x}
                    y={pos.y}
                    width={cardWidth}
                    height={cardHeight}
                    rx="3"
                    fill={style.fill}
                    stroke={style.stroke}
                    strokeWidth={style.strokeWidth}
                    className="card-shape"
                  />
                  {/* Contract text inside card */}
                  <text
                    x={pos.x + cardWidth / 2}
                    y={pos.y + cardHeight / 2 + 4}
                    textAnchor="middle"
                    className="card-contract-text"
                    fill={style.fill === 'white' ? style.stroke : 'white'}
                  >
                    {board.contract || `#${board.board_id}`}
                  </text>
                </g>
              );
            })
          )}

          {/* Overflow indicators */}
          {Object.entries(quadrants).map(([quadrantKey, quadrantBoards]) => {
            if (quadrantBoards.length <= 20) return null;
            const overflow = quadrantBoards.length - 20;
            const positions = {
              'top-right': { x: 340, y: 165 },
              'top-left': { x: 25, y: 165 },
              'bottom-right': { x: 340, y: 320 },
              'bottom-left': { x: 25, y: 320 }
            };
            const pos = positions[quadrantKey];
            return (
              <text
                key={`overflow-${quadrantKey}`}
                x={pos.x}
                y={pos.y}
                textAnchor={pos.x < 180 ? 'start' : 'end'}
                className="overflow-indicator"
              >
                +{overflow} more
              </text>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="board-analysis-legend">
        <div className="legend-title">Your Role:</div>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-card solid"></span>
            <span className="legend-label">You declared</span>
          </div>
          <div className="legend-item">
            <span className="legend-card hollow-thin"></span>
            <span className="legend-label">Partner declared</span>
          </div>
          <div className="legend-item">
            <span className="legend-card hollow-thick"></span>
            <span className="legend-label">You defended</span>
          </div>
        </div>

        {/* Domain legend - shows when any board has diagnostic_domain */}
        {boards.some(b => b.diagnostic_domain) && (
          <div className="domain-legend">
            <div className="legend-title">Learning Domain:</div>
            {boards.some(b => b.diagnostic_domain === 'safety') && (
              <div className="domain-legend-item">
                <span className="domain-dot safety"></span>
                <span>Safety (LoTT)</span>
              </div>
            )}
            {boards.some(b => b.diagnostic_domain === 'value') && (
              <div className="domain-legend-item">
                <span className="domain-dot value"></span>
                <span>Value</span>
              </div>
            )}
            {boards.some(b => b.diagnostic_domain === 'control') && (
              <div className="domain-legend-item">
                <span className="domain-dot control"></span>
                <span>Control</span>
              </div>
            )}
            {boards.some(b => b.diagnostic_domain === 'tactical') && (
              <div className="domain-legend-item">
                <span className="domain-dot tactical"></span>
                <span>Tactical</span>
              </div>
            )}
            {boards.some(b => b.diagnostic_domain === 'defensive') && (
              <div className="domain-legend-item">
                <span className="domain-dot defensive"></span>
                <span>Defensive</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tooltip */}
      {tooltip && (() => {
        const userScore = getScoreForUser(tooltip.board);
        const tricksDisplay = getTricksForUser(tooltip.board);
        const role = tooltip.board.user_was_declarer ? 'Declarer' : tooltip.board.user_was_dummy ? 'Dummy' : 'Defender';
        const declarerName = tooltip.board.declarer === 'N' ? 'North' :
                             tooltip.board.declarer === 'S' ? 'South' :
                             tooltip.board.declarer === 'E' ? 'East' : 'West';

        // Domain display for differential analysis
        const domainDisplay = {
          safety: { emoji: '⚠️', label: 'Safety (LoTT)' },
          value: { emoji: '💰', label: 'Value (Working HCP)' },
          control: { emoji: '🎯', label: 'Control (Trump)' },
          tactical: { emoji: '♟️', label: 'Tactical' },
          defensive: { emoji: '🛡️', label: 'Defensive' }
        };
        const domain = tooltip.board.diagnostic_domain ? domainDisplay[tooltip.board.diagnostic_domain] : null;

        return (
          <div
            className="board-tooltip"
            style={{
              position: 'fixed',
              left: tooltip.x,
              top: tooltip.y,
              transform: 'translate(-50%, -100%)'
            }}
          >
            <div className="tooltip-header">
              <strong>{tooltip.board.contract || `Board ${tooltip.board.board_id}`}</strong>
              <span> by {declarerName}</span>
            </div>
            <div className="tooltip-row">
              {tricksDisplay}
            </div>
            <div className="tooltip-row" style={{ fontWeight: 600, color: userScore >= 0 ? '#059669' : '#dc2626' }}>
              You: {userScore >= 0 ? '+' : ''}{userScore}
            </div>
            <div className="tooltip-row" style={{ fontSize: '11px', color: '#6b7280' }}>
              {role}
            </div>
            {domain && (
              <div className="tooltip-domain" style={{ fontSize: '11px', marginTop: '4px', padding: '2px 6px', background: '#f3f4f6', borderRadius: '4px' }}>
                {domain.emoji} {domain.label}
              </div>
            )}
            <div className="tooltip-hint">Click to review</div>
          </div>
        );
      })()}
    </div>
  );
};

// ============================================================================
// SHARED COMPONENTS
// ============================================================================

const SegmentedQualityBar = ({ good, suboptimal, error, labels = {} }) => {
  const goodLabel = labels.good || 'Good';
  const suboptimalLabel = labels.suboptimal || 'Needs Work';
  const errorLabel = labels.error || 'Errors';

  return (
    <div className="segmented-bar-container">
      <div className="segmented-bar">
        <div className="segment good" style={{ width: `${good}%` }} />
        <div className="segment suboptimal" style={{ width: `${suboptimal}%` }} />
        <div className="segment error" style={{ width: `${error}%` }} />
      </div>
      <div className="segment-labels">
        <span className="label good">{goodLabel} {good}%</span>
        <span className="label suboptimal">{suboptimalLabel} {suboptimal}%</span>
        <span className="label error">{errorLabel} {error}%</span>
      </div>
    </div>
  );
};

const HandRow = ({ hand, onReview }) => {
  // Handle both object contract format and string format from different APIs
  const contractLevel = hand.contract_level || hand.contract?.level || '';
  const contractStrain = hand.contract_strain || hand.contract?.strain || '';
  const contractStr = `${contractLevel}${contractStrain}`;

  // Get hand number within session for disambiguation
  const handNumber = hand.hand_number;

  // Determine role - API uses user_was_declarer/user_was_dummy
  const wasDeclarer = hand.user_was_declarer || hand.was_declarer;
  const wasDummy = hand.user_was_dummy || hand.was_dummy;
  const role = wasDeclarer ? 'Declarer' : wasDummy ? 'Dummy' : 'Defender';
  const isDefender = !wasDeclarer && !wasDummy;

  const quality = Math.round(hand.play_quality || 0);

  // Result comes as string ("+1", "-3", "=") from API
  // Parse it to determine display from user's perspective
  const getResultDisplay = () => {
    const resultStr = hand.result || '=';
    // Parse the result string to get numeric value
    let resultNum = 0;
    if (resultStr === '=' || resultStr === '0') {
      resultNum = 0;
    } else {
      resultNum = parseInt(resultStr, 10) || 0;
    }

    if (isDefender) {
      // As defender: positive result means they made overtricks (bad for us)
      // negative result means we set them (good for us)
      if (resultNum < 0) {
        return { text: `Set ${Math.abs(resultNum)}`, isGood: true };
      } else if (resultNum > 0) {
        return { text: `+${resultNum}`, isGood: false };
      } else {
        return { text: '=', isGood: false }; // Made exactly - not great for defender
      }
    } else {
      // As declarer/dummy: positive result is good
      if (resultNum > 0) {
        return { text: `+${resultNum}`, isGood: true };
      } else if (resultNum < 0) {
        return { text: `${resultNum}`, isGood: false };
      } else {
        return { text: '=', isGood: true }; // Made exactly - good for declarer
      }
    }
  };

  // Get score from NS (user's) perspective
  // User is always NS (South), so negate score when EW declares
  const getScoreDisplay = () => {
    let score = hand.score || 0;
    const declarer = hand.contract_declarer || hand.declarer;
    // If declarer was EW, negate the score for NS perspective
    if (declarer === 'E' || declarer === 'W') {
      score = -score;
    }
    return score > 0 ? `+${score}` : `${score}`;
  };

  // Get strain class for contract styling - uses standard red/black colors
  const getStrainClass = (strain) => {
    if (!strain) return '';
    if (strain.includes('♠') || strain === 'S') return 'spades';
    if (strain.includes('♥') || strain === 'H') return 'hearts';
    if (strain.includes('♦') || strain === 'D') return 'diamonds';
    if (strain.includes('♣') || strain === 'C') return 'clubs';
    if (strain.includes('NT') || strain === 'N') return 'notrump';
    return '';
  };

  const resultDisplay = getResultDisplay();
  const scoreDisplay = getScoreDisplay();
  const scoreNum = parseInt(scoreDisplay, 10) || 0;

  // Order: Hand#, Role, Contract, Result, Score, Quality%, Review button
  return (
    <div className="hand-row">
      {handNumber && <span className="hand-number">#{handNumber}</span>}
      <span className="role">{role}</span>
      <span className={`contract ${getStrainClass(contractStrain)}`}>{contractStr}</span>
      <span className={`result ${resultDisplay.isGood ? 'made' : 'down'}`}>{resultDisplay.text}</span>
      <span className={`score ${scoreNum >= 0 ? 'positive' : 'negative'}`}>{scoreDisplay}</span>
      <span className={`quality ${quality >= 70 ? 'good' : quality >= 50 ? 'suboptimal' : 'error'}`}>{quality}%</span>
      {onReview && (
        <button className="review-btn-primary" onClick={onReview}>Review</button>
      )}
    </div>
  );
};

// CategoryCard component - Hidden per user request (Play Categories section disabled)
// const CategoryCard = ({ category, data }) => {
//   const displayName = {
//     'opening_lead': 'Opening Lead',
//     'following_suit': 'Follow Suit',
//     'discarding': 'Discarding',
//     'trumping': 'Trumping',
//     'overruffing': 'Overruffing',
//     'sluffing': 'Sluffing',
//     'finessing': 'Finessing',
//     'cashing': 'Cashing',
//     'hold_up': 'Hold-Up',
//     'ducking': 'Ducking'
//   }[category] || category;
//
//   const accuracy = Math.round(data.accuracy || 0);
//   const skillLevel = data.skill_level || 'developing';
//
//   // Skill indicator dots
//   const dots = skillLevel === 'strong' ? 4 : skillLevel === 'good' ? 3 : skillLevel === 'developing' ? 2 : 1;
//
//   return (
//     <div className={`category-card skill-${skillLevel}`}>
//       <div className="category-name">{displayName}</div>
//       <div className="category-stats">
//         <span className="category-accuracy">{accuracy}%</span>
//         <span className="category-dots">
//           {[1, 2, 3, 4].map(i => (
//             <span key={i} className={`dot ${i <= dots ? 'filled' : ''}`}>●</span>
//           ))}
//         </span>
//       </div>
//       <div className="category-plays">{data.attempts} plays</div>
//     </div>
//   );
// };

export default FourDimensionProgress;
