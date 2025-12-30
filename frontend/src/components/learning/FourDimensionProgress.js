/**
 * Four-Dimension Progress Components
 *
 * Displays comprehensive learning progress across four dimensions:
 * 1. Bid Learning Journey - Structured bidding curriculum progress
 * 2. Bid Practice Quality - Freeplay bidding and convention mastery
 * 3. Play Learning Journey - Card play curriculum progress
 * 4. Play Practice Quality - Gameplay performance metrics
 */

import React, { useState, useEffect } from 'react';
import { getFourDimensionProgress } from '../../services/analyticsService';
import './FourDimensionProgress.css';

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const FourDimensionProgress = ({ userId, onStartLearning, onStartPractice }) => {
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('bidding'); // For mobile: 'bidding' | 'play'

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
      {/* Mobile Tab Switcher */}
      <div className="mobile-tab-switcher">
        <button
          className={`tab-button ${activeTab === 'bidding' ? 'active' : ''}`}
          onClick={() => setActiveTab('bidding')}
        >
          Bidding
        </button>
        <button
          className={`tab-button ${activeTab === 'play' ? 'active' : ''}`}
          onClick={() => setActiveTab('play')}
        >
          Card Play
        </button>
      </div>

      {/* Desktop: Two-column layout / Mobile: Tab content */}
      <div className="progress-columns">
        {/* Bidding Track */}
        <div className={`progress-track bidding-track ${activeTab === 'bidding' ? 'active' : ''}`}>
          <div className="track-header">
            <h3>Bidding Track</h3>
          </div>

          <JourneyProgressCard
            journey={bid_learning_journey}
            type="bidding"
            onStartLearning={() => onStartLearning?.('bidding')}
          />

          <PracticeQualityCard
            quality={bid_practice_quality}
            type="bidding"
            onStartPractice={() => onStartPractice?.('bidding')}
          />

          {bid_practice_quality.convention_mastery?.length > 0 && (
            <ConventionMasteryGrid
              conventions={bid_practice_quality.convention_mastery}
              currentLevel={bid_learning_journey.current_level}
            />
          )}
        </div>

        {/* Card Play Track */}
        <div className={`progress-track play-track ${activeTab === 'play' ? 'active' : ''}`}>
          <div className="track-header">
            <h3>Card Play Track</h3>
          </div>

          <JourneyProgressCard
            journey={play_learning_journey}
            type="play"
            onStartLearning={() => onStartLearning?.('play')}
          />

          <PracticeQualityCard
            quality={play_practice_quality}
            type="play"
            onStartPractice={() => onStartPractice?.('play')}
          />
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// JOURNEY PROGRESS CARD
// ============================================================================

const JourneyProgressCard = ({ journey, type, onStartLearning }) => {
  const {
    current_level,
    current_level_name,
    skills_in_level,
    skills_completed_in_level,
    total_skills_mastered,
    next_skill,
    progress_percentage,
    level_progress
  } = journey;

  // Calculate level progress percentage
  const levelPercentage = skills_in_level > 0
    ? Math.round((skills_completed_in_level / skills_in_level) * 100)
    : 0;

  return (
    <div className="dimension-card journey-card">
      <div className="card-header">
        <div className="card-title">
          <span className="card-icon">{type === 'bidding' ? '🎯' : '🃏'}</span>
          <h4>Learning Journey</h4>
        </div>
        <div className="overall-progress-badge">
          {Math.round(progress_percentage)}%
        </div>
      </div>

      <div className="card-content">
        {/* Current Level Progress Ring */}
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
              {total_skills_mastered} skills mastered
            </div>
          </div>
        </div>

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

        {/* Next Skill */}
        {next_skill && (
          <div className="next-skill">
            <span className="next-label">Next:</span>
            <span className="next-name">{next_skill.name}</span>
          </div>
        )}

        {/* Action Button */}
        <button className="journey-action-btn" onClick={onStartLearning}>
          Continue Learning
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// PRACTICE QUALITY CARD
// ============================================================================

const PracticeQualityCard = ({ quality, type, onStartPractice }) => {
  const isBidding = type === 'bidding';

  // Extract relevant stats based on type
  const mainMetric = isBidding
    ? quality.overall_accuracy
    : quality.declarer_success_rate;

  const trend = isBidding
    ? quality.recent_trend
    : quality.recent_trend;

  const totalPracticed = isBidding
    ? quality.total_decisions
    : quality.total_hands_played;

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
    <div className="dimension-card quality-card">
      <div className="card-header">
        <div className="card-title">
          <span className="card-icon">{isBidding ? '📊' : '🏆'}</span>
          <h4>Practice Quality</h4>
        </div>
        <div className={`trend-indicator ${getTrendClass(trend)}`}>
          {getTrendIcon(trend)} {trend}
        </div>
      </div>

      <div className="card-content">
        {/* Main Metric Gauge */}
        <div className="quality-gauge">
          <div className="gauge-value">{Math.round(mainMetric)}%</div>
          <div className="gauge-label">
            {isBidding ? 'Accuracy' : 'Success Rate'}
          </div>
          <div className="gauge-bar">
            <div
              className="gauge-fill"
              style={{ width: `${Math.min(mainMetric, 100)}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="quality-stats">
          {isBidding ? (
            <>
              <div className="stat-item">
                <span className="stat-value">{quality.optimal_rate}%</span>
                <span className="stat-label">Optimal</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{quality.error_rate}%</span>
                <span className="stat-label">Errors</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{quality.conventions_mastered}</span>
                <span className="stat-label">Conv. Mastered</span>
              </div>
            </>
          ) : (
            <>
              <div className="stat-item">
                <span className="stat-value">{quality.contracts_made}</span>
                <span className="stat-label">Made</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{quality.contracts_failed}</span>
                <span className="stat-label">Failed</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{quality.avg_tricks}</span>
                <span className="stat-label">Avg Tricks</span>
              </div>
            </>
          )}
        </div>

        {/* Total Practiced */}
        <div className="total-practiced">
          {totalPracticed} {isBidding ? 'decisions' : 'hands'} practiced
        </div>

        {/* Action Button */}
        <button className="quality-action-btn" onClick={onStartPractice}>
          Practice Now
        </button>
      </div>
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
    <div className="dimension-card convention-card">
      <div className="card-header">
        <div className="card-title">
          <span className="card-icon">🎓</span>
          <h4>Convention Mastery</h4>
        </div>
      </div>

      <div className="card-content">
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
