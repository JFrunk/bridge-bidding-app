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
import { getFourDimensionProgress, getDashboardData, getHandHistory } from '../../services/analyticsService';
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
      const [progress, dashboard, history] = await Promise.all([
        getFourDimensionProgress(userId),
        getDashboardData(userId).catch(() => null), // Dashboard data is optional
        getHandHistory(userId, 5).catch(() => ({ hands: [] })) // Hand history is optional
      ]);

      setProgressData(progress);
      setDashboardData(dashboard);
      setHandHistory(history.hands || []);
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
  const recentBidDecisions = dashboardData?.recent_decisions || [];

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
          miniStats={getPracticeBidMiniStats(bid_practice_quality)}
          actionLabel="Practice →"
          onAction={() => onStartPractice?.('bidding')}
          expanded={expandedBars['practice-bid']}
          onToggle={() => toggleBar('practice-bid')}
          accentColor="warning"
        >
          <PracticeBidExpanded
            quality={bid_practice_quality}
            recentDecisions={recentBidDecisions}
            onReviewHand={onReviewHand}
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
          miniStats={getPracticePlayMiniStats(play_practice_quality)}
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
          title="Performance Overview"
          miniStats={getPerformanceOverviewMiniStats(bid_practice_quality, play_practice_quality)}
          expanded={expandedBars['performance-overview']}
          onToggle={() => toggleBar('performance-overview')}
          accentColor="neutral"
        >
          <PerformanceOverviewExpanded
            bidQuality={bid_practice_quality}
            playQuality={play_practice_quality}
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

const getPracticeBidMiniStats = (quality) => {
  const avg = Math.round(quality?.overall_accuracy || 0);
  const trend = quality?.recent_trend || 'stable';
  const trendIcon = trend === 'improving' ? '↗' : trend === 'declining' ? '↘' : '→';
  const hands = quality?.total_decisions || 0;
  return `${avg}% avg • ${trendIcon} ${trend} • ${hands} hands`;
};

const getLearnPlayMiniStats = (journey) => {
  const level = journey?.current_level || 0;
  const skills = `${journey?.skills_completed_in_level || 0}/${journey?.skills_in_level || 0} skills`;
  const pct = Math.round(journey?.progress_percentage || 0);
  return `Level ${level} • ${skills} • ${pct}%`;
};

const getPracticePlayMiniStats = (quality) => {
  const playStats = quality?.play_decision_stats;
  const avg = Math.round(playStats?.optimal_rate || quality?.declarer_success_rate || 0);
  const trend = quality?.recent_trend || 'stable';
  const trendIcon = trend === 'improving' ? '↗' : trend === 'declining' ? '↘' : '→';
  const hands = quality?.total_hands_played || 0;
  return `${avg}% quality • ${trendIcon} ${trend} • ${hands} hands`;
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
    <div className={`progress-bar progress-bar-${accentColor} ${expanded ? 'expanded' : ''}`}>
      {/* Collapsed Header */}
      <div className="progress-bar-header" onClick={onToggle}>
        <div className="bar-left">
          <span className="bar-icon">{icon}</span>
          <span className="bar-title">{title}</span>
        </div>
        <div className="bar-center">
          <span className="bar-mini-stats">{miniStats}</span>
        </div>
        <div className="bar-right">
          {actionLabel && onAction && (
            <button
              className="bar-action-btn"
              onClick={(e) => {
                e.stopPropagation();
                onAction();
              }}
            >
              {actionLabel}
            </button>
          )}
          <span className={`bar-chevron ${expanded ? 'rotated' : ''}`}>▼</span>
        </div>
      </div>

      {/* Expanded Content */}
      <div className={`progress-bar-content ${expanded ? 'show' : ''}`}>
        {children}
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

const PracticeBidExpanded = ({ quality, recentDecisions, onReviewHand }) => {
  const goodRate = quality?.good_rate || 0;
  const suboptimalRate = quality?.suboptimal_rate || 0;
  const errorRate = quality?.error_rate || 0;
  const avgScore = Math.round(quality?.overall_accuracy || 0);

  return (
    <div className="expanded-content practice-bid-content">
      {/* Quality Breakdown with Segmented Bar */}
      <div className="quality-section">
        <div className="quality-header">
          <span className="quality-value">{avgScore}%</span>
          <span className="quality-label">Avg Score</span>
        </div>
        <SegmentedQualityBar
          good={goodRate}
          suboptimal={suboptimalRate}
          error={errorRate}
        />
      </div>

      {/* Recent Bidding Decisions */}
      {recentDecisions.length > 0 && (
        <div className="recent-decisions-section">
          <div className="section-header">
            <span className="section-title">Recent Bidding Decisions</span>
          </div>
          <div className="decisions-list">
            {recentDecisions.slice(0, 4).map((decision, idx) => (
              <DecisionRow
                key={decision.id || idx}
                decision={decision}
                onReview={() => onReviewHand?.(decision.hand_id)}
              />
            ))}
          </div>
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
  const playStats = quality?.play_decision_stats || {};
  const hasPlayData = playStats.optimal_rate > 0 || playStats.avg_score > 0;

  const goodRate = hasPlayData ? (playStats.good_rate || 0) : 0;
  const suboptimalRate = hasPlayData ? (playStats.suboptimal_rate || 0) : 0;
  const blunderRate = hasPlayData ? (playStats.blunder_rate || 0) : 0;
  const avgQuality = Math.round(hasPlayData ? playStats.optimal_rate : (quality?.declarer_success_rate || 0));

  // Category data now comes from play_decision_stats in the four-dimension progress API
  const tricksLost = playStats?.total_tricks_lost || 0;
  const categoryBreakdown = playStats?.category_breakdown || {};

  // Get top 6 categories by attempts
  const topCategories = Object.entries(categoryBreakdown)
    .filter(([_, data]) => data.attempts > 0)
    .sort((a, b) => b[1].attempts - a[1].attempts)
    .slice(0, 6);

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
            {onShowHandHistory && (
              <button className="see-all-btn" onClick={onShowHandHistory}>See All →</button>
            )}
          </div>
          <div className="hands-list">
            {handHistory.slice(0, 3).map((hand, idx) => (
              <HandRow
                key={hand.id || idx}
                hand={hand}
                onReview={() => onReviewHand?.(hand.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Play Categories Grid */}
      {topCategories.length > 0 && (
        <div className="categories-section">
          <div className="section-title">Play Categories</div>
          <div className="categories-grid">
            {topCategories.map(([category, data]) => (
              <CategoryCard key={category} category={category} data={data} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// PERFORMANCE OVERVIEW EXPANDED
// ============================================================================

const PerformanceOverviewExpanded = ({ bidQuality, playQuality }) => {
  const bidPct = Math.round(bidQuality?.overall_accuracy || 0);
  const playStats = playQuality?.play_decision_stats;
  const playPct = Math.round(playStats?.optimal_rate || playQuality?.declarer_success_rate || 0);

  // Determine quadrant
  const getQuadrantLabel = () => {
    if (bidPct >= 70 && playPct >= 70) return "Strong overall performance!";
    if (bidPct >= 70 && playPct < 70) return "Good bidding, focus on card play";
    if (bidPct < 70 && playPct >= 70) return "Good play, focus on bidding";
    return "Room to improve in both areas";
  };

  const getRecommendation = () => {
    if (bidPct >= 70 && playPct >= 70) return "Keep up the great work! Consider advancing to more complex conventions.";
    if (bidPct >= 70) return "Your bidding is solid! Focus on card play, especially finessing and discarding.";
    if (playPct >= 70) return "Your play is strong! Work on bidding fundamentals and convention usage.";
    return "Practice both bidding scenarios and complete hands to improve your overall game.";
  };

  return (
    <div className="expanded-content performance-overview-content">
      <div className="quadrant-section">
        <div className="section-title">Where Should You Focus?</div>

        {/* Quadrant Chart */}
        <div className="quadrant-chart">
          <svg viewBox="0 0 220 220" className="quadrant-svg">
            {/* Background quadrants */}
            <rect x="10" y="10" width="100" height="100" fill="#fef2f2" opacity="0.5" />
            <rect x="110" y="10" width="100" height="100" fill="#fffbeb" opacity="0.5" />
            <rect x="10" y="110" width="100" height="100" fill="#fffbeb" opacity="0.5" />
            <rect x="110" y="110" width="100" height="100" fill="#ecfdf5" opacity="0.5" />

            {/* Grid lines */}
            <line x1="110" y1="10" x2="110" y2="210" stroke="#e5e7eb" strokeWidth="1" />
            <line x1="10" y1="110" x2="210" y2="110" stroke="#e5e7eb" strokeWidth="1" />

            {/* Axis lines */}
            <line x1="10" y1="210" x2="210" y2="210" stroke="#9ca3af" strokeWidth="2" />
            <line x1="10" y1="10" x2="10" y2="210" stroke="#9ca3af" strokeWidth="2" />

            {/* Axis labels */}
            <text x="110" y="228" textAnchor="middle" className="axis-label">Bidding %</text>
            <text x="-110" y="5" textAnchor="middle" transform="rotate(-90)" className="axis-label">Play %</text>

            {/* Scale markers */}
            <text x="10" y="225" textAnchor="middle" className="scale-marker">0</text>
            <text x="110" y="225" textAnchor="middle" className="scale-marker">50</text>
            <text x="210" y="225" textAnchor="middle" className="scale-marker">100</text>

            {/* Data point */}
            <circle
              cx={10 + (bidPct * 2)}
              cy={210 - (playPct * 2)}
              r="10"
              fill="#3b82f6"
              stroke="#1d4ed8"
              strokeWidth="2"
            />

            {/* Quadrant labels */}
            <text x="55" y="55" textAnchor="middle" className="quadrant-label">Needs Work</text>
            <text x="160" y="55" textAnchor="middle" className="quadrant-label">Bid Well</text>
            <text x="55" y="165" textAnchor="middle" className="quadrant-label">Play Well</text>
            <text x="160" y="165" textAnchor="middle" className="quadrant-label">Strong</text>
          </svg>
        </div>

        {/* Stats Summary */}
        <div className="quadrant-stats">
          <div className="stat-row">
            <span className="stat-name">Bidding:</span>
            <span className={`stat-value ${bidPct >= 70 ? 'good' : 'needs-work'}`}>{bidPct}%</span>
          </div>
          <div className="stat-row">
            <span className="stat-name">Play:</span>
            <span className={`stat-value ${playPct >= 70 ? 'good' : 'needs-work'}`}>{playPct}%</span>
          </div>
        </div>

        {/* Recommendation */}
        <div className="recommendation-box">
          <span className="recommendation-icon">💡</span>
          <div className="recommendation-text">
            <strong>{getQuadrantLabel()}</strong>
            <p>{getRecommendation()}</p>
          </div>
        </div>
      </div>
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

const DecisionRow = ({ decision, onReview }) => {
  const correctnessIcon = {
    'optimal': '✓',
    'acceptable': '○',
    'suboptimal': '⚠',
    'error': '✗'
  }[decision.correctness] || '?';

  const correctnessClass = decision.correctness || 'unknown';

  return (
    <div className="decision-row">
      <span className={`correctness-icon ${correctnessClass}`}>{correctnessIcon}</span>
      <span className="decision-bids">
        {decision.user_bid}
        {decision.user_bid !== decision.optimal_bid && (
          <span className="optimal-bid"> → {decision.optimal_bid}</span>
        )}
      </span>
      <span className="decision-concept">{decision.key_concept}</span>
      <span className="decision-score">{decision.score}/10</span>
      {decision.hand_id && onReview && (
        <button className="review-link" onClick={onReview}>Review →</button>
      )}
    </div>
  );
};

const HandRow = ({ hand, onReview }) => {
  const contract = hand.contract || {};
  const contractStr = `${contract.level || ''}${contract.strain || ''}`;
  const resultStr = hand.result > 0 ? `+${hand.result}` : hand.result === 0 ? '=' : hand.result;
  const role = hand.was_declarer ? 'Declarer' : hand.was_dummy ? 'Dummy' : 'Defender';
  const score = hand.score > 0 ? `+${hand.score}` : hand.score;
  const quality = Math.round(hand.play_quality || 0);

  return (
    <div className="hand-row">
      <span className={`contract ${(contract.strain || '').toLowerCase()}`}>{contractStr}</span>
      <span className={`result ${hand.result >= 0 ? 'made' : 'down'}`}>{resultStr}</span>
      <span className="role">{role}</span>
      <span className="score">{score}</span>
      {quality > 0 && <span className="quality">{quality}%</span>}
      {onReview && (
        <button className="review-link" onClick={onReview}>Review →</button>
      )}
    </div>
  );
};

const CategoryCard = ({ category, data }) => {
  const displayName = {
    'opening_lead': 'Opening Lead',
    'following_suit': 'Follow Suit',
    'discarding': 'Discarding',
    'trumping': 'Trumping',
    'overruffing': 'Overruffing',
    'sluffing': 'Sluffing',
    'finessing': 'Finessing',
    'cashing': 'Cashing',
    'hold_up': 'Hold-Up',
    'ducking': 'Ducking'
  }[category] || category;

  const accuracy = Math.round(data.accuracy || 0);
  const skillLevel = data.skill_level || 'developing';

  // Skill indicator dots
  const dots = skillLevel === 'strong' ? 4 : skillLevel === 'good' ? 3 : skillLevel === 'developing' ? 2 : 1;

  return (
    <div className={`category-card skill-${skillLevel}`}>
      <div className="category-name">{displayName}</div>
      <div className="category-stats">
        <span className="category-accuracy">{accuracy}%</span>
        <span className="category-dots">
          {[1, 2, 3, 4].map(i => (
            <span key={i} className={`dot ${i <= dots ? 'filled' : ''}`}>●</span>
          ))}
        </span>
      </div>
      <div className="category-plays">{data.attempts} plays</div>
    </div>
  );
};

export default FourDimensionProgress;
