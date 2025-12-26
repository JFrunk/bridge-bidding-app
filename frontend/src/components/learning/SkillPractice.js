/**
 * Skill Practice Component
 *
 * Handles the practice session for a single skill:
 * - Shows the hand to evaluate
 * - Collects user's answer
 * - Shows feedback
 * - Tracks progress
 */

import React, { useState, useEffect } from 'react';
import './SkillPractice.css';

const SkillPractice = ({ session, onSubmitAnswer, onClose }) => {
  const [answer, setAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState(session?.lastResult || null);
  const [showFeedback, setShowFeedback] = useState(!!session?.lastResult);

  // Reset when hand changes
  useEffect(() => {
    if (session?.hand_id) {
      setAnswer('');
      setShowFeedback(!!session?.lastResult);
      setLastResult(session?.lastResult || null);
    }
  }, [session?.hand_id, session?.lastResult]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answer.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const result = await onSubmitAnswer(answer.trim());
      setLastResult({
        isCorrect: result.is_correct,
        feedback: result.feedback,
      });
      setShowFeedback(true);
    } catch (err) {
      console.error('Failed to submit answer:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleContinue = () => {
    setShowFeedback(false);
    setLastResult(null);
    setAnswer('');
  };

  if (!session) {
    return (
      <div className="skill-practice">
        <div className="error-state">
          <p>No active session</p>
          <button onClick={onClose}>Go Back</button>
        </div>
      </div>
    );
  }

  const { topic_id, hand, expected_response, progress } = session;
  const questionType = getQuestionType(expected_response);

  return (
    <div className="skill-practice">
      {/* Header */}
      <div className="practice-header">
        <button onClick={onClose} className="back-button">← Back</button>
        <h2 className="skill-title">{formatSkillName(topic_id)}</h2>
        <div className="progress-indicator">
          <span className="accuracy">{progress?.accuracy || 0}%</span>
          <span className="attempts">{progress?.correct || 0}/{progress?.attempts || 0}</span>
        </div>
      </div>

      {/* Hand Display */}
      <div className="hand-display-area">
        <div className="hand-card">
          <h3>Your Hand</h3>
          <pre className="hand-text">{hand?.display || 'No hand data'}</pre>
          <div className="hand-stats">
            <span>HCP: {hand?.hcp}</span>
            <span>Dist: {hand?.distribution_points}</span>
            <span>Total: {hand?.total_points}</span>
            <span>{hand?.is_balanced ? 'Balanced' : 'Unbalanced'}</span>
          </div>
        </div>
      </div>

      {/* Question Area */}
      <div className="question-area">
        <QuestionPrompt questionType={questionType} expected={expected_response} />

        {/* Answer Input */}
        {!showFeedback ? (
          <form onSubmit={handleSubmit} className="answer-form">
            <AnswerInput
              questionType={questionType}
              value={answer}
              onChange={setAnswer}
              disabled={isSubmitting}
            />
            <button
              type="submit"
              className="submit-button"
              disabled={!answer.trim() || isSubmitting}
            >
              {isSubmitting ? 'Checking...' : 'Submit'}
            </button>
          </form>
        ) : (
          <FeedbackDisplay
            result={lastResult}
            expected={expected_response}
            onContinue={handleContinue}
          />
        )}
      </div>
    </div>
  );
};

/**
 * Determine question type from expected response
 */
const getQuestionType = (expected) => {
  if (!expected) return 'unknown';
  if ('hcp' in expected && !('bid' in expected)) return 'hcp';
  if ('should_open' in expected) return 'should_open';
  if ('bid' in expected) return 'bidding';
  return 'unknown';
};

/**
 * Format skill ID to readable name
 */
const formatSkillName = (skillId) => {
  if (!skillId) return 'Practice';
  return skillId
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Question Prompt Component
 */
const QuestionPrompt = ({ questionType, expected }) => {
  const getPrompt = () => {
    switch (questionType) {
      case 'hcp':
        return 'How many High Card Points (HCP) does this hand have?';
      case 'should_open':
        return 'Should you open this hand?';
      case 'bidding':
        return 'What would you bid with this hand?';
      default:
        return 'Evaluate this hand:';
    }
  };

  return (
    <div className="question-prompt">
      <h3>{getPrompt()}</h3>
    </div>
  );
};

/**
 * Answer Input Component
 */
const AnswerInput = ({ questionType, value, onChange, disabled }) => {
  switch (questionType) {
    case 'hcp':
      return (
        <input
          type="number"
          className="answer-input hcp-input"
          placeholder="Enter HCP (0-40)"
          min="0"
          max="40"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          autoFocus
        />
      );

    case 'should_open':
      return (
        <div className="yes-no-buttons">
          <button
            type="button"
            className={`yn-button ${value === 'yes' ? 'selected' : ''}`}
            onClick={() => onChange('yes')}
            disabled={disabled}
          >
            Yes, Open
          </button>
          <button
            type="button"
            className={`yn-button ${value === 'no' ? 'selected' : ''}`}
            onClick={() => onChange('no')}
            disabled={disabled}
          >
            No, Pass
          </button>
        </div>
      );

    case 'bidding':
      return (
        <div className="bid-input-area">
          <input
            type="text"
            className="answer-input bid-input"
            placeholder="Enter bid (e.g., 1H, 2NT, Pass)"
            value={value}
            onChange={(e) => onChange(e.target.value.toUpperCase())}
            disabled={disabled}
            autoFocus
          />
          <div className="bid-shortcuts">
            {['1C', '1D', '1H', '1S', '1NT', '2C', '2NT', 'Pass'].map((bid) => (
              <button
                key={bid}
                type="button"
                className="bid-shortcut"
                onClick={() => onChange(bid)}
                disabled={disabled}
              >
                {formatBid(bid)}
              </button>
            ))}
          </div>
        </div>
      );

    default:
      return (
        <input
          type="text"
          className="answer-input"
          placeholder="Enter your answer"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          autoFocus
        />
      );
  }
};

/**
 * Format bid with suit symbols
 */
const formatBid = (bid) => {
  if (!bid) return bid;
  return bid
    .replace(/C/gi, '♣')
    .replace(/D/gi, '♦')
    .replace(/H/gi, '♥')
    .replace(/S/gi, '♠');
};

/**
 * Feedback Display Component
 */
const FeedbackDisplay = ({ result, expected, onContinue }) => {
  if (!result) return null;

  const { isCorrect, feedback } = result;

  return (
    <div className={`feedback-display ${isCorrect ? 'correct' : 'incorrect'}`}>
      <div className="feedback-icon">
        {isCorrect ? '✓' : '✗'}
      </div>
      <div className="feedback-content">
        <h4>{isCorrect ? 'Correct!' : 'Not quite...'}</h4>
        <p className="feedback-text">{feedback}</p>
        {expected?.explanation && !isCorrect && (
          <p className="explanation">{expected.explanation}</p>
        )}
      </div>
      <button onClick={onContinue} className="continue-button">
        Continue
      </button>
    </div>
  );
};

export default SkillPractice;
