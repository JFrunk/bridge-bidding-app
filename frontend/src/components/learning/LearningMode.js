/**
 * Learning Mode Component
 *
 * Main guided learning interface showing:
 * - Track selector (Bidding | Card Play)
 * - Skill tree with 10 levels (0-9) per track
 * - Progress through each level
 * - Skill practice sessions
 * - Level assessments
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './LearningMode.css';
import {
  getLearningStatus,
  getSkillTree,
  getUserSkillProgress,
  startLearningSession,
  submitLearningAnswer,
  getPlayLearningStatus,
  getPlaySkillTree,
  getUserPlayProgress,
  getPlayPracticeHand,
  recordPlayPractice,
  markSkillMastered,
} from '../../services/learningService';
import SkillPractice from './SkillPractice';
import SkillIntro from './SkillIntro';
import { useUser } from '../../contexts/UserContext';

const LearningMode = ({ userId, initialTrack = 'bidding' }) => {
  // Track selector: 'bidding' or 'play'
  const [selectedTrack, setSelectedTrack] = useState(initialTrack);
  const containerRef = useRef(null);

  // Get user experience level settings from context
  // Note: WelcomeWizard is now shown at app root level (App.js), not here
  const { isLevelUnlocked } = useUser();

  // Toast state for locked level clicks
  const [lockedToast, setLockedToast] = useState(null);

  const [learningStatus, setLearningStatus] = useState(null);
  const [skillTree, setSkillTree] = useState(null);
  const [skillProgress, setSkillProgress] = useState({}); // Map of skill_id -> status
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [showingIntro, setShowingIntro] = useState(null); // { skillId, skillName, track }

  const loadData = useCallback(async () => {
    if (!userId) return;
    try {
      setLoading(true);
      setError(null);

      let status, tree, progress;

      if (selectedTrack === 'bidding') {
        [status, tree, progress] = await Promise.all([
          getLearningStatus(userId),
          getSkillTree(),
          getUserSkillProgress(userId),
        ]);
      } else {
        // Card Play track
        [status, tree, progress] = await Promise.all([
          getPlayLearningStatus(userId),
          getPlaySkillTree(),
          getUserPlayProgress(userId),
        ]);
      }

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
  }, [userId, selectedLevel, selectedTrack]);

  // Load learning status and skill tree
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Scroll to top helper
  const scrollToTop = useCallback(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
    window.scrollTo(0, 0);
  }, []);

  // Handle track switching
  const handleTrackChange = (track) => {
    if (track !== selectedTrack) {
      setSelectedTrack(track);
      setSelectedLevel(null); // Reset selected level when switching tracks
      setLearningStatus(null);
      setSkillTree(null);
      setSkillProgress({});
      scrollToTop();
    }
  };

  const handleStartSkill = (skillId, skillName) => {
    // Show intro screen first, include track info
    setShowingIntro({ skillId, skillName, track: selectedTrack });
  };

  const handleStartPractice = async () => {
    if (!showingIntro) return;

    try {
      let session;

      if (showingIntro.track === 'play') {
        // Play skill - use play practice hand API
        const playData = await getPlayPracticeHand(showingIntro.skillId);
        session = {
          topic_id: showingIntro.skillId,
          topic_type: 'play_skill',
          track: 'play',
          deal: playData.deal,
          situation: playData.situation,
          hand_id: playData.hand_id,
          skill_level: playData.skill_level,
          practice_format: playData.practice_format,
          // For play skills, expected_response comes from situation
          // Include wrong_answers and explanation at the expected_response level for feedback
          expected_response: {
            ...playData.situation.expected_response,
            explanation: playData.situation.explanation,
            wrong_answers: playData.situation.wrong_answers,
          },
          progress: { attempts: 0, correct: 0, accuracy: 0, status: 'not_started' },
        };
      } else {
        // Bidding skill - use existing session API
        session = await startLearningSession(userId, showingIntro.skillId, 'skill');
      }

      setActiveSession({
        ...session,
        skillId: showingIntro.skillId,
        track: showingIntro.track,
        // Track hand history for navigation
        handHistory: [{
          hand: session.hand,
          deal: session.deal,
          hand_id: session.hand_id,
          expected_response: session.expected_response,
          situation: session.situation,
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
    scrollToTop();
  };

  const handleSubmitAnswer = async (answer) => {
    if (!activeSession) return;

    try {
      let result;

      if (activeSession.track === 'play') {
        // Play skill - evaluate locally and record practice
        const expected = activeSession.expected_response;

        // Determine answer type and evaluate accordingly
        let isCorrect = false;
        let correctAnswer;
        let userAnswer;

        if (expected.card) {
          // Card-based answer (third_hand_high, etc.)
          correctAnswer = expected.card;
          // Normalize user input: convert full names to single letters
          const normalized = answer.trim().toUpperCase()
            .replace('ACE', 'A')
            .replace('KING', 'K')
            .replace('QUEEN', 'Q')
            .replace('JACK', 'J')
            .replace('10', 'T')
            .replace('TEN', 'T');

          userAnswer = normalized[0]; // Take first character after normalization
          isCorrect = userAnswer === correctAnswer;
        } else {
          // Numeric answer (counting winners, losers, etc.)
          userAnswer = parseInt(answer, 10);
          correctAnswer = expected.winners ?? expected.losers ?? expected.correct_answer;

          // Check if answer is correct (within acceptable range if provided)
          if (expected.acceptable_range) {
            isCorrect = userAnswer >= expected.acceptable_range[0] &&
                        userAnswer <= expected.acceptable_range[1];
          } else {
            isCorrect = userAnswer === correctAnswer;
          }
        }

        // Generate feedback — use wrong-answer-specific rationale when available
        let feedback;
        if (isCorrect) {
          feedback = `Correct! ${expected.explanation || ''}`;
        } else {
          const wrongRationale = expected.wrong_answers?.[userAnswer];
          feedback = wrongRationale
            ? `The correct answer is ${correctAnswer}. ${wrongRationale}`
            : `The correct answer is ${correctAnswer}. ${expected.explanation || ''}`;
        }

        // Record the practice attempt
        const recordResult = await recordPlayPractice({
          user_id: userId,
          skill_id: activeSession.skillId,
          skill_level: activeSession.skill_level || 0,
          was_correct: isCorrect,
          hand_id: activeSession.hand_id,
          user_answer: String(answer),
          correct_answer: String(correctAnswer),
        });

        // Get next hand for play skill
        const nextPlayData = await getPlayPracticeHand(activeSession.skillId);

        result = {
          is_correct: isCorrect,
          feedback,
          progress: recordResult.progress || activeSession.progress,
          is_mastered: recordResult.is_mastered || false,
          next_hand: null, // Play skills use deal instead
          next_deal: nextPlayData.deal,
          next_situation: nextPlayData.situation,
          next_hand_id: nextPlayData.hand_id,
          next_expected: {
            ...nextPlayData.situation.expected_response,
            explanation: nextPlayData.situation.explanation,
            wrong_answers: nextPlayData.situation.wrong_answers,
          },
        };
      } else {
        // Bidding skill - use existing API
        result = await submitLearningAnswer({
          user_id: userId,
          topic_id: activeSession.skillId,
          topic_type: 'skill',
          answer,
          hand_id: activeSession.hand_id,
          expected_response: activeSession.expected_response,
        });
      }

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

      // Per-session mastery check (replaces cumulative mastery)
      const SESSION_MIN_HANDS = 6;
      const SESSION_MAX_HANDS = 10;
      const SESSION_PASSING_ACCURACY = 0.80;

      const answered = updatedHistory.filter(h => h.result !== null).length;
      const correct = updatedHistory.filter(h => h.result?.isCorrect === true).length;
      const accuracy = answered > 0 ? correct / answered : 0;

      let sessionOutcome = null; // null | 'mastered' | 'keep_practicing'
      if (answered >= SESSION_MIN_HANDS && accuracy >= SESSION_PASSING_ACCURACY) {
        sessionOutcome = 'mastered';
      } else if (answered >= SESSION_MAX_HANDS) {
        sessionOutcome = 'keep_practicing';
      }

      if (sessionOutcome) {
        // Session complete — show summary, no next hand needed
        setActiveSession({
          ...activeSession,
          progress: result.progress,
          lastResult: {
            isCorrect: result.is_correct,
            feedback: result.feedback,
          },
          sessionComplete: sessionOutcome,
          sessionAccuracy: accuracy,
          sessionHands: answered,
          handHistory: updatedHistory,
        });
      } else {
        // Session continues — prepare next hand
        const pendingNext = activeSession.track === 'play'
          ? {
              deal: result.next_deal,
              hand_id: result.next_hand_id,
              expected_response: result.next_expected,
              situation: result.next_situation,
            }
          : (result.next_hand || result.next_expected) ? {
              hand: result.next_hand,
              hand_id: result.next_hand_id,
              expected_response: result.next_expected,
            } : null;

        setActiveSession({
          ...activeSession,
          progress: result.progress,
          lastResult: {
            isCorrect: result.is_correct,
            feedback: result.feedback,
          },
          pendingNext,
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
    scrollToTop();
  };

  const handleContinue = async () => {
    if (!activeSession) return;

    // Session complete — mark mastery if achieved, then close
    if (activeSession.sessionComplete) {
      if (activeSession.sessionComplete === 'mastered') {
        try {
          await markSkillMastered({
            user_id: userId,
            skill_id: activeSession.skillId,
            track: activeSession.track || 'bidding',
            session_accuracy: activeSession.sessionAccuracy,
            session_hands: activeSession.sessionHands,
          });
        } catch (err) {
          console.error('Failed to mark skill mastered:', err);
        }
      }
      setActiveSession(null);
      loadData();
      scrollToTop();
      return;
    }

    // Apply pending next hand and add to history
    if (activeSession.pendingNext) {
      const isPlayTrack = activeSession.track === 'play';

      const newHistoryEntry = {
        hand: activeSession.pendingNext.hand,
        deal: activeSession.pendingNext.deal,
        hand_id: activeSession.pendingNext.hand_id,
        expected_response: activeSession.pendingNext.expected_response,
        situation: activeSession.pendingNext.situation,
        result: null,
      };

      setActiveSession({
        ...activeSession,
        hand: activeSession.pendingNext.hand,
        deal: isPlayTrack ? activeSession.pendingNext.deal : activeSession.deal,
        hand_id: activeSession.pendingNext.hand_id,
        expected_response: activeSession.pendingNext.expected_response,
        situation: activeSession.pendingNext.situation,
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
      deal: historyEntry.deal,
      hand_id: historyEntry.hand_id,
      expected_response: historyEntry.expected_response,
      situation: historyEntry.situation,
      currentHandIndex: index,
      // If reviewing a past hand, show its result
      lastResult: historyEntry.result,
      isReviewing: index < activeSession.handHistory.length - 1 || historyEntry.result !== null,
    });
  };

  // Handle locked level click - show toast message
  // Must be defined before early returns to satisfy React hooks rules
  const handleLockedLevelClick = useCallback((levelNumber) => {
    const prevLevel = levelNumber - 1;
    setLockedToast({
      message: `Complete Level ${prevLevel} to unlock, or adjust your Experience Level in settings.`,
      key: Date.now()
    });
    // Auto-dismiss after 4 seconds
    setTimeout(() => setLockedToast(null), 4000);
  }, []);

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
    <>
      {/* Toast notification for locked levels */}
      {lockedToast && (
        <div className="locked-toast" key={lockedToast.key}>
          <span className="locked-toast-icon">🔒</span>
          <span className="locked-toast-message">{lockedToast.message}</span>
          <button
            className="locked-toast-close"
            onClick={() => setLockedToast(null)}
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      )}

      <div className="learning-mode" ref={containerRef}>
        {/* Header - simplified since TopNavigation provides main navigation */}
        <div className="learning-mode-header">
          <div className="header-content">
            <h1>Learning Mode</h1>
            <p className="subtitle">
              {selectedTrack === 'bidding'
                ? 'Master bridge bidding step by step'
                : 'Master declarer play techniques'}
            </p>
          </div>
        </div>

        {/* Track Selector Tabs */}
        <div className="track-selector">
          <button
            className={`track-tab ${selectedTrack === 'bidding' ? 'active' : ''}`}
            onClick={() => handleTrackChange('bidding')}
            data-testid="track-bidding"
          >
            <span className="track-icon">🎯</span>
            <span className="track-label">Bidding</span>
          </button>
          <button
            className={`track-tab ${selectedTrack === 'play' ? 'active' : ''}`}
            onClick={() => handleTrackChange('play')}
            data-testid="track-play"
          >
            <span className="track-icon">♠</span>
            <span className="track-label">Card Play</span>
          </button>
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
              isLevelUnlocked={isLevelUnlocked}
              onLockedClick={handleLockedLevelClick}
            />
          ))}
        </div>
      </div>
    </>
  );
};

/**
 * Level Card Component
 *
 * Locking logic combines:
 * 1. User's experience level (from WelcomeWizard/Settings)
 * 2. Whether previous level is completed
 * 3. Whether areAllLevelsUnlocked is true
 */
const LevelCard = ({
  levelId,
  levelData,
  skillTree,
  skillProgress,
  isSelected,
  onSelect,
  onStartSkill,
  isLevelUnlocked,
  onLockedClick
}) => {
  const {
    name,
    level_number,
    completed,
    total,
    percentage,
    unlocked: backendUnlocked, // Backend's unlock status (based on progress)
    is_convention_group,
  } = levelData;

  // Skill tree API returns levels directly as keys, not nested under 'levels'
  const levelInfo = skillTree?.[levelId] || {};
  const skills = levelInfo.skills || [];
  const conventions = levelInfo.conventions || [];

  // NEW: Combined unlock logic
  // A level is unlocked if:
  // 1. User's experience level allows it (isLevelUnlocked from context), OR
  // 2. Backend says it's unlocked (completed previous level)
  const isUnlocked = isLevelUnlocked(level_number) || backendUnlocked;

  const getStatusClass = () => {
    if (!isUnlocked) return 'locked';
    if (completed === total) return 'completed';
    if (completed > 0) return 'in-progress';
    return '';
  };

  // Handle click - either select or show locked message
  const handleClick = () => {
    if (isUnlocked) {
      onSelect();
    } else {
      onLockedClick(level_number);
    }
  };

  return (
    <div
      className={`level-card ${getStatusClass()} ${isSelected ? 'selected' : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      <div className="level-card-header">
        <div className="level-number">Level {level_number}</div>
        {!isUnlocked && <div className="level-status-icon">🔒</div>}
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

      {/* Show skills for all levels — unlocked get practice buttons, locked get dimmed preview */}
      <div className={`level-skills ${!isUnlocked ? 'level-skills-locked' : ''}`}>
        {is_convention_group ? (
          <div className="convention-list">
            {conventions.map((convention) => (
              <div key={convention.id} className={`skill-item ${!isUnlocked ? 'skill-item-locked' : ''}`}>
                <span className="skill-name">{convention.name}</span>
                {isUnlocked && (
                  <button
                    className="practice-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onStartSkill(convention.id, convention.name);
                    }}
                  >
                    Practice
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="skill-list">
            {skills.map((skill) => (
              isUnlocked ? (
                <SkillItem
                  key={skill.id}
                  skill={skill}
                  status={skillProgress[skill.id] || 'not_started'}
                  onStart={() => onStartSkill(skill.id, skill.name)}
                />
              ) : (
                <div key={skill.id} className="skill-item skill-item-locked">
                  <span className="skill-name">{skill.name}</span>
                </div>
              )
            ))}
          </div>
        )}
      </div>
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
