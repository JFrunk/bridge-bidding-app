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
import { getFourDimensionProgress, getDashboardData, getHandHistory, getBoardAnalysis } from '../../services/analyticsService';
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
          title="Board Analysis"
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
      <div className={`expandable-progress-bar-content ${expanded ? 'show' : ''}`}>
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
// BOARD ANALYSIS EXPANDED - Pianola-style Performance Chart
// ============================================================================

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

  // Group boards by quadrant
  const quadrants = {
    'strong': [],      // good bidding + good play (top-right)
    'bid-focus': [],   // good bidding, bad play (top-left)
    'play-focus': [],  // bad bidding, good play (bottom-right)
    'review': []       // bad bidding + bad play (bottom-left)
  };

  boards.forEach(board => {
    const playGood = board.play_quality === 'good';
    const bidGood = board.bidding_quality === 'good';

    if (bidGood && playGood) quadrants['strong'].push(board);
    else if (bidGood && !playGood) quadrants['bid-focus'].push(board);
    else if (!bidGood && playGood) quadrants['play-focus'].push(board);
    else quadrants['review'].push(board);
  });

  // Grid packing: position boards in rows within each quadrant
  const getGridPosition = (quadrantKey, index) => {
    const cols = 5;
    const row = Math.floor(index / cols);
    const col = index % cols;
    const spacingX = 26;
    const spacingY = 24;

    // Quadrant centers (in 320x280 SVG)
    const centers = {
      'strong': { x: 240, y: 70 },
      'bid-focus': { x: 80, y: 70 },
      'play-focus': { x: 240, y: 210 },
      'review': { x: 80, y: 210 }
    };

    const center = centers[quadrantKey];
    return {
      x: center.x - 52 + col * spacingX,
      y: center.y - 24 + row * spacingY
    };
  };

  // Our distinctive color palette (teal/amber/indigo/rose - NOT green/yellow/red)
  const quadrantColors = {
    'strong': { badge: '#0d9488', bg: '#ccfbf1', bgEnd: '#99f6e4' },      // teal
    'bid-focus': { badge: '#f59e0b', bg: '#fef3c7', bgEnd: '#fde68a' },   // amber
    'play-focus': { badge: '#6366f1', bg: '#e0e7ff', bgEnd: '#c7d2fe' },  // indigo
    'review': { badge: '#e11d48', bg: '#ffe4e6', bgEnd: '#fecdd3' }       // rose
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
      {/* Session Filter */}
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

      {/* Board Analysis Chart */}
      <div className="board-analysis-chart-container">
        <svg viewBox="0 0 320 280" className="board-analysis-chart">
          {/* Gradient definitions */}
          <defs>
            {Object.entries(quadrantColors).map(([key, colors]) => (
              <linearGradient key={key} id={`gradient-${key}`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={colors.bg} />
                <stop offset="100%" stopColor={colors.bgEnd} />
              </linearGradient>
            ))}
          </defs>

          {/* Quadrant backgrounds with rounded corners */}
          <rect x="4" y="4" width="152" height="132" rx="8" fill="url(#gradient-bid-focus)" />
          <rect x="164" y="4" width="152" height="132" rx="8" fill="url(#gradient-strong)" />
          <rect x="4" y="144" width="152" height="132" rx="8" fill="url(#gradient-review)" />
          <rect x="164" y="144" width="152" height="132" rx="8" fill="url(#gradient-play-focus)" />

          {/* X-axis: Card Play with Bad/Good labels */}
          <text x="160" y="290" textAnchor="middle" className="chart-axis-label">Card Play</text>
          <text x="4" y="290" textAnchor="start" className="chart-axis-marker">Bad</text>
          <text x="316" y="290" textAnchor="end" className="chart-axis-marker">Good</text>

          {/* Y-axis: Bidding with Bad/Good labels */}
          <text x="10" y="140" textAnchor="middle" transform="rotate(-90, 10, 140)" className="chart-axis-label">Bidding</text>
          <text x="10" y="276" textAnchor="middle" transform="rotate(-90, 10, 276)" className="chart-axis-marker">Bad</text>
          <text x="10" y="16" textAnchor="middle" transform="rotate(-90, 10, 16)" className="chart-axis-marker">Good</text>

          {/* Quadrant labels with bridge suit icons */}
          <text x="80" y="20" textAnchor="middle" className="chart-quadrant-title">♥ Focus: Play</text>
          <text x="240" y="20" textAnchor="middle" className="chart-quadrant-title">♠ Strong</text>
          <text x="80" y="262" textAnchor="middle" className="chart-quadrant-title">♣ Review</text>
          <text x="240" y="262" textAnchor="middle" className="chart-quadrant-title">♦ Focus: Bidding</text>

          {/* Board badges */}
          {Object.entries(quadrants).map(([quadrantKey, quadrantBoards]) =>
            quadrantBoards.slice(0, 20).map((board, index) => {
              const pos = getGridPosition(quadrantKey, index);
              const colors = quadrantColors[quadrantKey];

              return (
                <g
                  key={board.hand_id}
                  className="board-badge"
                  onClick={() => handleBoardClick(board.hand_id)}
                  onMouseEnter={(e) => handleMouseEnter(e, board)}
                  onMouseLeave={handleMouseLeave}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Pill-shaped badge */}
                  <rect
                    x={pos.x - 11}
                    y={pos.y - 9}
                    width="22"
                    height="18"
                    rx="4"
                    fill={colors.badge}
                    className="badge-bg"
                  />
                  {/* Contract or board number */}
                  <text
                    x={pos.x}
                    y={pos.y + 4}
                    textAnchor="middle"
                    className="badge-text"
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
              'strong': { x: 308, y: 130 },
              'bid-focus': { x: 12, y: 130 },
              'play-focus': { x: 308, y: 270 },
              'review': { x: 12, y: 270 }
            };
            const pos = positions[quadrantKey];
            return (
              <text
                key={`overflow-${quadrantKey}`}
                x={pos.x}
                y={pos.y}
                textAnchor={pos.x < 160 ? 'start' : 'end'}
                className="overflow-indicator"
              >
                +{overflow}
              </text>
            );
          })}
        </svg>
      </div>

      {/* Summary Stats */}
      <div className="board-analysis-summary">
        <div className="summary-item strong">
          <span className="summary-count">{summary.good_good}</span>
          <span className="summary-label">Strong</span>
        </div>
        <div className="summary-item bid-focus">
          <span className="summary-count">{summary.good_bad}</span>
          <span className="summary-label">Focus: Play</span>
        </div>
        <div className="summary-item play-focus">
          <span className="summary-count">{summary.bad_good}</span>
          <span className="summary-label">Focus: Bid</span>
        </div>
        <div className="summary-item review">
          <span className="summary-count">{summary.bad_bad}</span>
          <span className="summary-label">Review</span>
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
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
            {tooltip.board.declarer && <span> by {tooltip.board.declarer}</span>}
          </div>
          <div className="tooltip-row">
            Tricks: {tooltip.board.actual_tricks}/{tooltip.board.dd_tricks} (DD)
          </div>
          <div className="tooltip-row">
            Score: {tooltip.board.actual_score} (Par: {tooltip.board.par_score})
          </div>
          <div className="tooltip-hint">Click to review</div>
        </div>
      )}
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
