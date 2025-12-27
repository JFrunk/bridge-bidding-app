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
  getUserSkillProgress,
  startLearningSession,
  submitLearningAnswer,
} from '../../services/learningService';
import SkillPractice from './SkillPractice';
import SkillIntro from './SkillIntro';

const LearningMode = ({ userId, onClose, onPlayFreePlay }) => {
  const [learningStatus, setLearningStatus] = useState(null);
  const [skillTree, setSkillTree] = useState(null);
  const [skillProgress, setSkillProgress] = useState({}); // Map of skill_id -> status
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [showingIntro, setShowingIntro] = useState(null); // { skillId, skillName }

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [status, tree, progress] = await Promise.all([
        getLearningStatus(userId),
        getSkillTree(),
        getUserSkillProgress(userId),
      ]);
      setLearningStatus(status);
      setSkillTree(tree);

      // Build a map of skill_id -> status for easy lookup
      const progressMap = {};
      if (progress.skills) {
        progress.skills.forEach(skill => {
          progressMap[skill.skill_id] = skill.status;
        });
      }
      setSkillProgress(progressMap);

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

  const handleStartSkill = (skillId, skillName) => {
    // Show intro screen first
    setShowingIntro({ skillId, skillName });
  };

  const handleStartPractice = async () => {
    if (!showingIntro) return;

    try {
      const session = await startLearningSession(userId, showingIntro.skillId, 'skill');
      setActiveSession({
        ...session,
        skillId: showingIntro.skillId,
        // Track hand history for navigation
        handHistory: [{
          hand: session.hand,
          hand_id: session.hand_id,
          expected_response: session.expected_response,
          result: null, // Will be filled after user answers
        }],
        currentHandIndex: 0,
      });
      setShowingIntro(null);
    } catch (err) {
      setError(err.message);
      setShowingIntro(null);
    }
  };

  const handleBackFromIntro = () => {
    setShowingIntro(null);
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

      // Update history with result for current hand
      const updatedHistory = [...activeSession.handHistory];
      updatedHistory[activeSession.currentHandIndex] = {
        ...updatedHistory[activeSession.currentHandIndex],
        result: {
          isCorrect: result.is_correct,
          feedback: result.feedback,
          userAnswer: answer,
        },
      };

      // Store result and next hand info, but DON'T change the current hand yet
      // The hand will be updated when user clicks "Continue" in SkillPractice
      if (result.is_mastered) {
        // Skill mastered - store this info, will close session on Continue
        setActiveSession({
          ...activeSession,
          progress: result.progress,
          lastResult: {
            isCorrect: result.is_correct,
            feedback: result.feedback,
          },
          isMastered: true,
          handHistory: updatedHistory,
        });
      } else {
        // Store result but keep current hand visible
        // Next hand data is stored in pendingNext for when user clicks Continue
        setActiveSession({
          ...activeSession,
          progress: result.progress,
          lastResult: {
            isCorrect: result.is_correct,
            feedback: result.feedback,
          },
          pendingNext: result.next_hand ? {
            hand: result.next_hand,
            hand_id: result.next_hand_id,
            expected_response: result.next_expected,
          } : null,
          handHistory: updatedHistory,
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

  const handleContinue = () => {
    if (!activeSession) return;

    // Check if skill was mastered
    if (activeSession.isMastered) {
      // Close session and show completion
      setActiveSession(null);
      loadData();
      return;
    }

    // Apply pending next hand and add to history
    if (activeSession.pendingNext) {
      const newHistoryEntry = {
        hand: activeSession.pendingNext.hand,
        hand_id: activeSession.pendingNext.hand_id,
        expected_response: activeSession.pendingNext.expected_response,
        result: null,
      };

      setActiveSession({
        ...activeSession,
        hand: activeSession.pendingNext.hand,
        hand_id: activeSession.pendingNext.hand_id,
        expected_response: activeSession.pendingNext.expected_response,
        lastResult: null,
        pendingNext: null,
        handHistory: [...activeSession.handHistory, newHistoryEntry],
        currentHandIndex: activeSession.handHistory.length,
      });
    }
  };

  // Navigate to a specific hand in history (for review)
  const handleNavigateHand = (index) => {
    if (!activeSession || index < 0 || index >= activeSession.handHistory.length) return;

    const historyEntry = activeSession.handHistory[index];
    setActiveSession({
      ...activeSession,
      hand: historyEntry.hand,
      hand_id: historyEntry.hand_id,
      expected_response: historyEntry.expected_response,
      currentHandIndex: index,
      // If reviewing a past hand, show its result
      lastResult: historyEntry.result,
      isReviewing: index < activeSession.handHistory.length - 1 || historyEntry.result !== null,
    });
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

  // Show skill intro before practice
  if (showingIntro) {
    return (
      <SkillIntro
        skillId={showingIntro.skillId}
        skillName={showingIntro.skillName}
        onStart={handleStartPractice}
        onBack={handleBackFromIntro}
      />
    );
  }

  // Show skill practice if session is active
  if (activeSession) {
    return (
      <SkillPractice
        session={activeSession}
        onSubmitAnswer={handleSubmitAnswer}
        onContinue={handleContinue}
        onClose={handleCloseSession}
        onNavigateHand={handleNavigateHand}
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
            skillProgress={skillProgress}
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
const LevelCard = ({ levelId, levelData, skillTree, skillProgress, isSelected, onSelect, onStartSkill }) => {
  const {
    name,
    level_number,
    completed,
    total,
    percentage,
    unlocked,
    is_convention_group,
  } = levelData;

  // Skill tree API returns levels directly as keys, not nested under 'levels'
  const levelInfo = skillTree?.[levelId] || {};
  const skills = levelInfo.skills || [];
  const conventions = levelInfo.conventions || [];

  const getStatusClass = () => {
    if (!unlocked) return 'locked';
    if (completed === total) return 'completed';
    if (completed > 0) return 'in-progress';
    return '';
  };

  return (
    <div
      className={`level-card ${getStatusClass()} ${isSelected ? 'selected' : ''}`}
      onClick={unlocked ? onSelect : undefined}
    >
      <div className="level-card-header">
        <div className="level-number">Level {level_number}</div>
        {!unlocked && <div className="level-status-icon">🔒</div>}
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

      {/* Always show skills for unlocked levels so users can see progress and retry */}
      {unlocked && (
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
                      onStartSkill(convId, convId);
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
                  status={skillProgress[skill.id] || 'not_started'}
                  onStart={() => onStartSkill(skill.id, skill.name)}
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
const SkillItem = ({ skill, status, onStart }) => {
  const { name, practice_hands_required, passing_accuracy } = skill;

  // Status indicator styling
  const getStatusIndicator = () => {
    switch (status) {
      case 'mastered':
        return { icon: '✓', className: 'status-mastered' };
      case 'in_progress':
        return { icon: '◐', className: 'status-in-progress' };
      default:
        return { icon: '○', className: 'status-not-started' };
    }
  };

  const statusInfo = getStatusIndicator();

  return (
    <div className={`skill-item ${statusInfo.className}`}>
      <div className="skill-status-indicator">{statusInfo.icon}</div>
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
        {status === 'mastered' ? 'Review' : 'Practice'}
      </button>
    </div>
  );
};

export default LearningMode;
