/**
 * Four-Dimension Progress Components
 *
 * Displays comprehensive learning progress across four sections that align
 * with navigation: Learn Bid, Practice Bid, Learn Play, Practice Play
 *
 * Layout: 2x2 grid on desktop, stacked on mobile
 */

import React, { useState, useEffect } from 'react';
import { getFourDimensionProgress } from '../../services/analyticsService';
import './FourDimensionProgress.css';

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const FourDimensionProgress = ({ userId, onStartLearning, onStartPractice, onShowHandHistory }) => {
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProgress();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const loadProgress = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFourDimensionProgress(userId);
      setProgressData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="four-dimension-loading">
        <div className="loading-spinner"></div>
        <p>Loading your progress...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="four-dimension-error">
        <span className="error-icon">!</span>
        <p>Failed to load progress: {error}</p>
        <button onClick={loadProgress}>Retry</button>
      </div>
    );
  }

  if (!progressData) {
    return null;
  }

  const { bid_learning_journey, bid_practice_quality, play_learning_journey, play_practice_quality } = progressData;

  return (
    <div className="four-dimension-progress">
      {/* 2x2 Grid: Learn Bid, Practice Bid, Learn Play, Practice Play */}
      <div className="progress-grid">
        {/* Row 1: Bidding */}
        <ProgressCard
          type="learn-bid"
          icon="📚"
          title="Learn Bid"
          journey={bid_learning_journey}
          onAction={() => onStartLearning?.('bidding')}
          actionLabel="Continue Learning"
        />

        <ProgressCard
          type="practice-bid"
          icon="🎲"
          title="Practice Bid"
          quality={bid_practice_quality}
          qualityType="bidding"
          onAction={() => onStartPractice?.('bidding')}
          actionLabel="Practice Now"
        />

        {/* Row 2: Card Play */}
        <ProgressCard
          type="learn-play"
          icon="🃏"
          title="Learn Play"
          journey={play_learning_journey}
          onAction={() => onStartLearning?.('play')}
          actionLabel="Continue Learning"
        />

        <ProgressCard
          type="practice-play"
          icon="♠"
          title="Practice Play"
          quality={play_practice_quality}
          qualityType="play"
          onAction={() => onStartPractice?.('play')}
          actionLabel="Practice Now"
          onShowHandHistory={onShowHandHistory}
        />
      </div>

      {/* Convention Mastery Section - Full width below grid */}
      {bid_practice_quality.convention_mastery?.length > 0 && (
        <ConventionMasteryGrid
          conventions={bid_practice_quality.convention_mastery}
          currentLevel={bid_learning_journey.current_level}
        />
      )}
    </div>
  );
};

// ============================================================================
// UNIFIED PROGRESS CARD
// ============================================================================

const ProgressCard = ({
  type,
  icon,
  title,
  journey,
  quality,
  qualityType,
  onAction,
  actionLabel,
  onShowHandHistory
}) => {
  const isJourneyCard = !!journey;
  const isQualityCard = !!quality;

  return (
    <div className={`progress-card progress-card-${type}`}>
      <div className="card-header">
        <div className="card-title">
          <span className="card-icon">{icon}</span>
          <h4>{title}</h4>
        </div>
        {isJourneyCard && (
          <div className="overall-progress-badge">
            {Math.round(journey.progress_percentage)}%
          </div>
        )}
        {isQualityCard && (
          <TrendIndicator trend={quality.recent_trend} />
        )}
      </div>

      <div className="card-content">
        {isJourneyCard && (
          <JourneyContent journey={journey} />
        )}
        {isQualityCard && (
          <QualityContent quality={quality} type={qualityType} onShowHandHistory={onShowHandHistory} />
        )}

        <button
          className={`card-action-btn ${isJourneyCard ? 'primary' : 'secondary'}`}
          onClick={onAction}
        >
          {actionLabel}
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// JOURNEY CONTENT (for Learn Bid / Learn Play cards)
// ============================================================================

const JourneyContent = ({ journey }) => {
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
  } = journey;

  const levelPercentage = skills_in_level > 0
    ? Math.round((skills_completed_in_level / skills_in_level) * 100)
    : 0;

  return (
    <>
      {/* Current Level Progress */}
      <div className="level-progress-section">
        <div className="progress-ring-container">
          <svg className="progress-ring" viewBox="0 0 100 100">
            <circle
              className="progress-ring-bg"
              cx="50"
              cy="50"
              r="42"
              fill="none"
              strokeWidth="8"
            />
            <circle
              className="progress-ring-fill"
              cx="50"
              cy="50"
              r="42"
              fill="none"
              strokeWidth="8"
              strokeDasharray={`${levelPercentage * 2.64} 264`}
              strokeLinecap="round"
              transform="rotate(-90 50 50)"
            />
            <text x="50" y="45" textAnchor="middle" className="ring-level">
              L{current_level}
            </text>
            <text x="50" y="62" textAnchor="middle" className="ring-progress">
              {skills_completed_in_level}/{skills_in_level}
            </text>
          </svg>
        </div>
        <div className="level-details">
          <div className="level-name">{current_level_name}</div>
          <div className="skills-mastered">
            {total_skills_mastered > 0 ? (
              `${total_skills_mastered} skills mastered`
            ) : skills_in_progress > 0 ? (
              `${skills_in_progress} skill${skills_in_progress > 1 ? 's' : ''} in progress`
            ) : (
              'Ready to start!'
            )}
          </div>
        </div>
      </div>

      {/* Current Skill Progress - Show when user is actively practicing */}
      {current_skill_progress && current_skill_progress.attempts > 0 && (
        <div className="current-skill-progress">
          <div className="skill-progress-header">
            <span className="skill-label">Current:</span>
            <span className="skill-name">{next_skill?.name || current_skill_progress.skill_id}</span>
          </div>
          <div className="skill-progress-stats">
            <span className="stat">{current_skill_progress.attempts} attempts</span>
            <span className="stat">{current_skill_progress.accuracy}% accuracy</span>
          </div>
          <div className="skill-progress-bar">
            <div
              className="skill-progress-fill"
              style={{ width: `${Math.min(current_skill_progress.accuracy, 100)}%` }}
            />
          </div>
          <div className="skill-progress-hint">
            {current_skill_progress.accuracy >= 80
              ? 'Almost mastered!'
              : `Need 80% accuracy to master (${5 - current_skill_progress.attempts} more hands min)`
            }
          </div>
        </div>
      )}

      {/* Level Roadmap */}
      <div className="level-roadmap">
        {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((level) => {
          const levelId = Object.keys(level_progress).find(
            (id) => level_progress[id].level === level
          );
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

      {/* Next Skill - Only show if not already showing current progress */}
      {next_skill && (!current_skill_progress || current_skill_progress.attempts === 0) && (
        <div className="next-skill">
          <span className="next-label">Next:</span>
          <span className="next-name">{next_skill.name}</span>
          {next_skill.in_progress && next_skill.attempts > 0 && (
            <span className="in-progress-badge">
              {next_skill.attempts} done, {next_skill.accuracy}%
            </span>
          )}
        </div>
      )}
    </>
  );
};

// ============================================================================
// QUALITY CONTENT (for Practice Bid / Practice Play cards)
// ============================================================================

const QualityContent = ({ quality, type, onShowHandHistory }) => {
  const isBidding = type === 'bidding';

  // For play: prefer DDS-based play_decision_stats if available, else use gameplay stats
  const playDecisionStats = !isBidding ? quality.play_decision_stats : null;
  const hasPlayDecisionData = playDecisionStats && (playDecisionStats.optimal_rate > 0 || playDecisionStats.avg_score > 0);

  // Main metric: bidding uses overall_accuracy, play uses optimal_rate from DDS or declarer_success_rate
  const mainMetric = isBidding
    ? quality.overall_accuracy
    : hasPlayDecisionData
      ? playDecisionStats.optimal_rate  // DDS-based optimal play rate
      : quality.declarer_success_rate;

  // Total practiced: bidding uses decisions, play uses DDS analyzed plays or hands played
  const totalPracticed = isBidding
    ? quality.total_decisions
    : hasPlayDecisionData
      ? (quality.total_hands_played || 0) + ' hands'  // From gameplay
      : quality.total_hands_played;

  // Determine color class based on score
  const getScoreClass = (score) => {
    if (score >= 70) return 'score-high';
    if (score >= 50) return 'score-medium';
    return 'score-low';
  };

  return (
    <>
      {/* Main Metric Gauge */}
      <div className="quality-gauge">
        <div className="gauge-value">{Math.round(mainMetric || 0)}%</div>
        <div className="gauge-label">
          {isBidding ? 'Accuracy' : (hasPlayDecisionData ? 'Play Quality' : 'Success Rate')}
        </div>
        <div className="gauge-bar">
          <div
            className={`gauge-fill ${getScoreClass(mainMetric || 0)}`}
            style={{ width: `${Math.min(mainMetric || 0, 100)}%` }}
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="quality-stats">
        {isBidding ? (
          <>
            <div className="stat-item">
              <span className="stat-value">{quality.optimal_rate || 0}%</span>
              <span className="stat-label">Optimal</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{quality.error_rate || 0}%</span>
              <span className="stat-label">Errors</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{quality.conventions_mastered || 0}</span>
              <span className="stat-label">Conv.</span>
            </div>
          </>
        ) : hasPlayDecisionData ? (
          // DDS-based play quality stats
          <>
            <div className="stat-item">
              <span className="stat-value">{Math.round(playDecisionStats.avg_score * 10) || 0}%</span>
              <span className="stat-label">Avg Score</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{Math.round(playDecisionStats.blunder_rate) || 0}%</span>
              <span className="stat-label">Blunders</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{quality.contracts_made || 0}/{quality.contracts_failed || 0}</span>
              <span className="stat-label">Made/Down</span>
            </div>
          </>
        ) : (
          // Fallback: session-based gameplay stats
          <>
            <div className="stat-item">
              <span className="stat-value">{quality.contracts_made || 0}</span>
              <span className="stat-label">Made</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{quality.contracts_failed || 0}</span>
              <span className="stat-label">Failed</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{quality.avg_tricks || 0}</span>
              <span className="stat-label">Avg Tricks</span>
            </div>
          </>
        )}
      </div>

      {/* Total Practiced */}
      <div className="total-practiced">
        {isBidding
          ? `${totalPracticed || 0} decisions practiced`
          : hasPlayDecisionData
            ? (
              <span
                className="hands-link"
                onClick={(e) => {
                  e.stopPropagation();
                  onShowHandHistory?.();
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && onShowHandHistory?.()}
              >
                {quality.total_hands_played || 0} hands analyzed →
              </span>
            )
            : `${totalPracticed || 0} hands practiced`
        }
      </div>
    </>
  );
};

// ============================================================================
// TREND INDICATOR
// ============================================================================

const TrendIndicator = ({ trend }) => {
  const getTrendIcon = (t) => {
    switch (t) {
      case 'improving': return '↗';
      case 'declining': return '↘';
      default: return '→';
    }
  };

  const getTrendClass = (t) => {
    switch (t) {
      case 'improving': return 'trend-improving';
      case 'declining': return 'trend-declining';
      default: return 'trend-stable';
    }
  };

  return (
    <div className={`trend-indicator ${getTrendClass(trend)}`}>
      {getTrendIcon(trend)} {trend || 'stable'}
    </div>
  );
};

// ============================================================================
// CONVENTION MASTERY GRID
// ============================================================================

const ConventionMasteryGrid = ({ conventions, currentLevel }) => {
  // Group conventions by level (essential=5, intermediate=7, advanced=8)
  const essential = conventions.filter((c) => c.level === 'essential');
  const intermediate = conventions.filter((c) => c.level === 'intermediate');
  const advanced = conventions.filter((c) => c.level === 'advanced');

  // Determine which groups to show (current level + 1 ahead)
  const showIntermediate = currentLevel >= 5;
  const showAdvanced = currentLevel >= 7;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'mastered': return '✓';
      case 'in_progress': return '◐';
      default: return '○';
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'mastered': return 'status-mastered';
      case 'in_progress': return 'status-in-progress';
      default: return 'status-not-started';
    }
  };

  const ConventionItem = ({ conv }) => (
    <div className={`convention-item ${getStatusClass(conv.status)}`}>
      <span className="conv-status">{getStatusIcon(conv.status)}</span>
      <span className="conv-name">{conv.name}</span>
      {conv.attempts > 0 && (
        <span className="conv-accuracy">{conv.accuracy}%</span>
      )}
    </div>
  );

  return (
    <div className="convention-mastery-section">
      <div className="convention-header">
        <span className="convention-icon">🎓</span>
        <h4>Convention Mastery</h4>
      </div>

      <div className="convention-content">
        {/* Essential Conventions (Level 5) */}
        {essential.length > 0 && (
          <div className="convention-group">
            <div className="group-header">
              <span className="group-name">Essential</span>
              <span className="group-count">
                {essential.filter((c) => c.status === 'mastered').length}/{essential.length}
              </span>
            </div>
            <div className="convention-list">
              {essential.map((conv) => (
                <ConventionItem key={conv.id} conv={conv} />
              ))}
            </div>
          </div>
        )}

        {/* Intermediate Conventions (Level 7) */}
        {showIntermediate && intermediate.length > 0 && (
          <div className="convention-group">
            <div className="group-header">
              <span className="group-name">Intermediate</span>
              <span className="group-count">
                {intermediate.filter((c) => c.status === 'mastered').length}/{intermediate.length}
              </span>
            </div>
            <div className="convention-list">
              {intermediate.map((conv) => (
                <ConventionItem key={conv.id} conv={conv} />
              ))}
            </div>
          </div>
        )}

        {/* Advanced Preview (Level 8) */}
        {showAdvanced && advanced.length > 0 && (
          <div className="convention-group">
            <div className="group-header">
              <span className="group-name">Advanced</span>
              <span className="group-count">
                {advanced.filter((c) => c.status === 'mastered').length}/{advanced.length}
              </span>
            </div>
            <div className="convention-list">
              {advanced.map((conv) => (
                <ConventionItem key={conv.id} conv={conv} />
              ))}
            </div>
          </div>
        )}

        {/* Locked Preview */}
        {!showIntermediate && (
          <div className="locked-preview">
            <span className="lock-icon">🔒</span>
            <span>Complete Level 5 to unlock more conventions</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default FourDimensionProgress;
