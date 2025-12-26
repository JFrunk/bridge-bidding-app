/**
 * Learning Mode Component
 *
 * Main guided learning interface showing:
 * - Skill tree with 9 levels (0-8)
 * - Progress through each level
 * - Skill practice sessions
 * - Level assessments
 */

import React, { useState, useEffect, useCallback } from 'react';
import './LearningMode.css';
import {
  getLearningStatus,
  getSkillTree,
  startLearningSession,
  submitLearningAnswer,
} from '../../services/learningService';
import SkillPractice from './SkillPractice';

const LearningMode = ({ userId, onClose, onPlayFreePlay }) => {
  const [learningStatus, setLearningStatus] = useState(null);
  const [skillTree, setSkillTree] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [activeSession, setActiveSession] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [status, tree] = await Promise.all([
        getLearningStatus(userId),
        getSkillTree(),
      ]);
      setLearningStatus(status);
      setSkillTree(tree);

      // Auto-select current level if none selected
      if (!selectedLevel && status.current_level) {
        setSelectedLevel(status.current_level);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [userId, selectedLevel]);

  // Load learning status and skill tree
  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStartSkill = async (skillId) => {
    try {
      const session = await startLearningSession(userId, skillId, 'skill');
      setActiveSession({
        ...session,
        skillId,
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSubmitAnswer = async (answer) => {
    if (!activeSession) return;

    try {
      const result = await submitLearningAnswer({
        user_id: userId,
        topic_id: activeSession.skillId,
        topic_type: 'skill',
        answer,
        hand_id: activeSession.hand_id,
        expected_response: activeSession.expected_response,
      });

      // Update session with result and next hand
      if (result.is_mastered) {
        // Skill mastered - close session and refresh
        setActiveSession(null);
        loadData();
      } else if (result.next_hand) {
        // Continue with next hand
        setActiveSession({
          ...activeSession,
          hand: result.next_hand,
          hand_id: result.next_hand_id,
          expected_response: result.next_expected,
          progress: result.progress,
          lastResult: {
            isCorrect: result.is_correct,
            feedback: result.feedback,
          },
        });
      }

      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const handleCloseSession = () => {
    setActiveSession(null);
    loadData(); // Refresh progress
  };

  if (loading) {
    return (
      <div className="learning-mode">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading your learning journey...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="learning-mode">
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <h3>Something went wrong</h3>
          <p>{error}</p>
          <button onClick={loadData} className="retry-button">Try Again</button>
        </div>
      </div>
    );
  }

  // Show skill practice if session is active
  if (activeSession) {
    return (
      <SkillPractice
        session={activeSession}
        onSubmitAnswer={handleSubmitAnswer}
        onClose={handleCloseSession}
      />
    );
  }

  const levels = learningStatus?.levels || {};
  const overallProgress = learningStatus?.overall_progress || { completed: 0, total: 0, percentage: 0 };

  return (
    <div className="learning-mode">
      {/* Header */}
      <div className="learning-mode-header">
        <div className="header-content">
          <h1>Learning Mode</h1>
          <p className="subtitle">Master bridge bidding step by step</p>
        </div>
        <div className="header-actions">
          <button onClick={onPlayFreePlay} className="free-play-button">
            Free Play
          </button>
          <button onClick={onClose} className="close-button">×</button>
        </div>
      </div>

      {/* Overall Progress */}
      <div className="overall-progress-bar">
        <div className="progress-info">
          <span className="progress-label">Overall Progress</span>
          <span className="progress-value">{overallProgress.completed} / {overallProgress.total} skills</span>
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${overallProgress.percentage}%` }}
          ></div>
        </div>
        <span className="progress-percentage">{overallProgress.percentage.toFixed(1)}%</span>
      </div>

      {/* Level Grid */}
      <div className="level-grid">
        {Object.entries(levels).map(([levelId, levelData]) => (
          <LevelCard
            key={levelId}
            levelId={levelId}
            levelData={levelData}
            skillTree={skillTree}
            isSelected={selectedLevel === levelId}
            onSelect={() => setSelectedLevel(levelId)}
            onStartSkill={handleStartSkill}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Level Card Component
 */
const LevelCard = ({ levelId, levelData, skillTree, isSelected, onSelect, onStartSkill }) => {
  const {
    name,
    level_number,
    completed,
    total,
    percentage,
    unlocked,
    is_convention_group,
  } = levelData;

  const levelInfo = skillTree?.levels?.[levelId] || {};
  const skills = levelInfo.skills || [];
  const conventions = levelInfo.conventions || [];

  const getStatusClass = () => {
    if (!unlocked) return 'locked';
    if (completed === total) return 'completed';
    if (completed > 0) return 'in-progress';
    return 'unlocked';
  };

  const getStatusIcon = () => {
    if (!unlocked) return '🔒';
    if (completed === total) return '✅';
    if (completed > 0) return '📚';
    return '▶️';
  };

  return (
    <div
      className={`level-card ${getStatusClass()} ${isSelected ? 'selected' : ''}`}
      onClick={unlocked ? onSelect : undefined}
    >
      <div className="level-card-header">
        <div className="level-number">Level {level_number}</div>
        <div className="level-status-icon">{getStatusIcon()}</div>
      </div>

      <h3 className="level-name">{name}</h3>

      <div className="level-progress">
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <span className="progress-text">{completed}/{total}</span>
      </div>

      {/* Expanded Skills (when selected) */}
      {isSelected && unlocked && (
        <div className="level-skills">
          {is_convention_group ? (
            <div className="convention-list">
              {conventions.map((convId) => (
                <div key={convId} className="skill-item">
                  <span className="skill-name">{convId}</span>
                  <button
                    className="practice-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onStartSkill(convId);
                    }}
                  >
                    Practice
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="skill-list">
              {skills.map((skill) => (
                <SkillItem
                  key={skill.id}
                  skill={skill}
                  onStart={() => onStartSkill(skill.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Skill Item Component
 */
const SkillItem = ({ skill, onStart }) => {
  const { name, practice_hands_required, passing_accuracy } = skill;

  return (
    <div className="skill-item">
      <div className="skill-info">
        <span className="skill-name">{name}</span>
        <span className="skill-meta">
          {practice_hands_required} hands • {Math.round(passing_accuracy * 100)}% to pass
        </span>
      </div>
      <button
        className="practice-button"
        onClick={(e) => {
          e.stopPropagation();
          onStart();
        }}
      >
        Practice
      </button>
    </div>
  );
};

export default LearningMode;
