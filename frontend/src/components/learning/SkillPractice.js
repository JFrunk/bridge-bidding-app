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
import { LearningHand } from './LearningCard';
import { TermHighlight } from '../glossary';

const SkillPractice = ({ session, onSubmitAnswer, onContinue, onClose, onNavigateHand }) => {
  const [answer, setAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState(session?.lastResult || null);
  const [showFeedback, setShowFeedback] = useState(!!session?.lastResult);
  const [showHandStats, setShowHandStats] = useState(false);
  const [isReplaying, setIsReplaying] = useState(false);

  // Sync local state when navigating between hands
  // This handles both new hands and reviewing previous hands
  useEffect(() => {
    if (session?.hand_id) {
      setAnswer('');
      setShowHandStats(false);
      setIsReplaying(false);

      // Sync feedback state with current hand's result
      if (session.lastResult) {
        setLastResult(session.lastResult);
        setShowFeedback(true);
      } else {
        setLastResult(null);
        setShowFeedback(false);
      }
    }
  }, [session?.hand_id, session?.currentHandIndex, session?.lastResult]);

  // Handle replay - reset answer and hide feedback to try again
  const handleReplay = () => {
    setAnswer('');
    setShowFeedback(false);
    setIsReplaying(true);
    // Note: We don't reset lastResult so we can track it was a replay
  };

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
    // Reset local state
    setShowFeedback(false);
    setLastResult(null);
    setAnswer('');
    // Tell parent to load next hand
    if (onContinue) {
      onContinue();
    }
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

  const { topic_id, hand, deal, situation, expected_response, progress, handHistory, currentHandIndex, isReviewing, track } = session;
  const isPlayTrack = track === 'play';
  const questionType = isPlayTrack ? getPlayQuestionType(situation) : getQuestionType(expected_response);
  const noHandRequired = expected_response?.no_hand_required || (!hand && !deal);

  // Calculate hand progress
  // Minimum is 6 hands, but can be more if accuracy isn't met
  const minHands = 6;
  const currentHandNumber = (currentHandIndex ?? 0) + 1;

  // Calculate SESSION-specific stats from handHistory (not cumulative from DB)
  // This shows progress within the current practice session
  const sessionAnswered = handHistory?.filter(h => h.result !== null).length || 0;
  const sessionCorrect = handHistory?.filter(h => h.result?.isCorrect === true).length || 0;
  const sessionAccuracy = sessionAnswered > 0 ? Math.round((sessionCorrect / sessionAnswered) * 100) : 0;

  // Show "Hand X of Y" if under minimum, just "Hand X" if exceeded
  const showTotal = (handHistory?.length || 0) < minHands;

  // Build array of 6 slots for dots, filling with history data where available
  const handSlots = Array.from({ length: Math.max(minHands, handHistory?.length || 0) }, (_, i) => {
    if (handHistory && i < handHistory.length) {
      return handHistory[i];
    }
    return null; // Future hand slot
  });

  return (
    <div className="skill-practice">
      {/* Header */}
      <div className="practice-header">
        <button onClick={onClose} className="back-button">← Back</button>
        <h2 className="skill-title">{formatSkillName(topic_id, expected_response)}</h2>
        <div className="progress-indicator">
          <div className="progress-stats">
            <span className="hand-counter">
              {showTotal ? `Hand ${currentHandNumber} of ${minHands}` : `Hand ${currentHandNumber}`}
            </span>
            {sessionAnswered > 0 && (
              <span className="accuracy-label">
                Accuracy: <span className="accuracy-value">{sessionAccuracy}%</span>
              </span>
            )}
          </div>
          {sessionAnswered > 0 && (
            <span className="score-display">{sessionCorrect} correct of {sessionAnswered} this session</span>
          )}
        </div>
      </div>

      {/* Hand Navigation - always show dots (at least 6) */}
      <div className="hand-navigation">
        <button
          className="nav-arrow"
          onClick={() => onNavigateHand(currentHandIndex - 1)}
          disabled={!handHistory || currentHandIndex <= 0}
          aria-label="Previous hand"
        >
          ‹
        </button>
        <div className="hand-dots">
          {handSlots.map((entry, index) => {
            const isAccessible = handHistory && index < handHistory.length;
            const isCurrent = index === currentHandIndex;
            const isCorrect = entry?.result?.isCorrect === true;
            const isIncorrect = entry?.result?.isCorrect === false;
            const isFuture = !isAccessible;

            return (
              <button
                key={index}
                className={`hand-dot ${isCurrent ? 'active' : ''} ${isCorrect ? 'correct' : ''} ${isIncorrect ? 'incorrect' : ''} ${isFuture ? 'future' : ''}`}
                onClick={() => isAccessible && onNavigateHand(index)}
                disabled={isFuture}
                aria-label={`Hand ${index + 1}${entry?.result ? (isCorrect ? ' - correct' : ' - incorrect') : isFuture ? ' - not yet attempted' : ''}`}
              >
                {index + 1}
              </button>
            );
          })}
        </div>
        <button
          className="nav-arrow"
          onClick={() => onNavigateHand(currentHandIndex + 1)}
          disabled={!handHistory || currentHandIndex >= handHistory.length - 1}
          aria-label="Next hand"
        >
          ›
        </button>
      </div>

      {/* Hand Display - only show if hand is required */}
      {!noHandRequired && (
        <div className="hand-display-area">
          {/* Play skills: Show both declarer and dummy hands */}
          {isPlayTrack && deal ? (
            <div className="play-deal-display">
              {/* Contract info */}
              {deal.contract && (
                <div className="contract-info">
                  <span className="contract-label">Contract:</span>
                  <span className="contract-value">{deal.contract}</span>
                  <span className="combined-hcp">Combined: {deal.combined_hcp} HCP</span>
                </div>
              )}
              <div className="dual-hand-display">
                {/* Dummy hand (North) */}
                <div className="hand-card visual-hand dummy-hand">
                  <h3>Dummy (North)</h3>
                  {deal.dummy_hand?.cards && deal.dummy_hand.cards.length > 0 ? (
                    <LearningHand cards={deal.dummy_hand.cards} size="medium" />
                  ) : (
                    <pre className="hand-text">{deal.dummy_hand?.display || 'No hand data'}</pre>
                  )}
                  <div className="hand-stats">
                    <span>HCP: {deal.dummy_hand?.hcp}</span>
                  </div>
                </div>
                {/* Declarer hand (South) */}
                <div className="hand-card visual-hand declarer-hand">
                  <h3>Declarer (South)</h3>
                  {deal.declarer_hand?.cards && deal.declarer_hand.cards.length > 0 ? (
                    <LearningHand cards={deal.declarer_hand.cards} size="medium" />
                  ) : (
                    <pre className="hand-text">{deal.declarer_hand?.display || 'No hand data'}</pre>
                  )}
                  <div className="hand-stats">
                    <span>HCP: {deal.declarer_hand?.hcp}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Bidding skills: Show single hand */
            <div className="hand-card visual-hand">
              <h3>Your Hand</h3>
              {/* Visual card display - matches main app styling */}
              {hand?.cards && hand.cards.length > 0 ? (
                <LearningHand cards={hand.cards} size="medium" />
              ) : (
                <pre className="hand-text">{hand?.display || 'No hand data'}</pre>
              )}
              {/* Hide stats by default - user can reveal if desired */}
              <div className="hand-stats-toggle">
                {showHandStats || showFeedback ? (
                  <div className="hand-stats">
                    <span>HCP: {hand?.hcp}</span>
                    <span>Dist: {hand?.distribution_points}</span>
                    <span>Total: {hand?.total_points}</span>
                    <span>{hand?.is_balanced ? 'Balanced' : 'Unbalanced'}</span>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="reveal-stats-button"
                    onClick={() => setShowHandStats(true)}
                  >
                    Show Hand Stats
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Question Area */}
      <div className={`question-area ${noHandRequired ? 'centered' : ''}`}>
        <QuestionPrompt questionType={questionType} expected={expected_response} situation={situation} />

        {/* Answer Input */}
        {!showFeedback ? (
          <form onSubmit={handleSubmit} className="answer-form">
            <AnswerInput
              questionType={questionType}
              expected={expected_response}
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
            onReplay={handleReplay}
            isReviewing={isReviewing}
            isReplaying={isReplaying}
            canContinue={!isReviewing || currentHandIndex === (handHistory?.length || 1) - 1}
          />
        )}
      </div>
    </div>
  );
};

/**
 * Determine question type from expected response (bidding skills)
 */
const getQuestionType = (expected) => {
  if (!expected) return 'unknown';
  if ('hcp' in expected && !('bid' in expected) && !('game_points_needed' in expected)) return 'hcp';
  if ('should_open' in expected) return 'should_open';
  if ('bid' in expected) return 'bidding';
  if ('longest_suit' in expected) return 'longest_suit';
  if ('game_points_needed' in expected) return 'game_points';
  // Contract-specific game/slam points (bidding_language skill)
  if ('correct_answer' in expected && expected.no_hand_required) return 'contract_points';
  return 'unknown';
};

/**
 * Determine question type from situation (play skills)
 */
const getPlayQuestionType = (situation) => {
  if (!situation) return 'unknown';
  const questionType = situation.question_type;
  if (questionType === 'count_winners') return 'count_winners';
  if (questionType === 'count_losers') return 'count_losers';
  if (questionType === 'analyze_lead') return 'analyze_lead';
  if (questionType === 'finesse_direction') return 'finesse_direction';
  if (questionType === 'finesse_or_drop') return 'finesse_or_drop';
  if (questionType === 'establish_suit') return 'establish_suit';
  if (questionType === 'hold_up') return 'hold_up';
  if (questionType === 'draw_trumps') return 'draw_trumps';
  if (questionType === 'ruff_losers') return 'ruff_losers';
  return 'play_numeric'; // Default for most play skills
};

/**
 * Format skill ID to readable, descriptive name for learners
 * Uses explicit descriptions instead of just converting underscores
 */
const formatSkillName = (skillId, expectedResponse = null) => {
  if (!skillId) return 'Practice';

  // Dynamic titles based on partner's opening (when available)
  if (expectedResponse?.partner_opened) {
    const partnerBid = expectedResponse.partner_opened;

    if (skillId === 'responding_to_major') {
      return `Responding to Partner's ${partnerBid} Opening`;
    }
    if (skillId === 'responding_to_minor') {
      return `Responding to Partner's ${partnerBid} Opening`;
    }
  }

  // Explicit skill name mappings for clarity
  const skillNames = {
    // === BIDDING SKILLS ===
    // Level 0: Foundations
    'hand_evaluation_basics': 'Hand Evaluation Basics',
    'suit_quality': 'Understanding Suit Quality',
    'bidding_language': 'The Language of Bidding',

    // Level 1: Opening Bids
    'when_to_open': 'When to Open the Bidding',
    'opening_one_suit': 'Opening One of a Suit',
    'opening_1nt': 'Opening 1 No Trump (1NT)',
    'opening_2c_strong': 'Opening 2 Clubs (Strong)',
    'opening_2nt': 'Opening 2 No Trump (2NT)',

    // Level 2: Responding
    'responding_to_major': 'Responding to a Major Suit Opening (1♥/1♠)',
    'responding_to_minor': 'Responding to a Minor Suit Opening (1♣/1♦)',
    'responding_to_1nt': 'Responding to 1NT Opening',
    'responding_to_2c': 'Responding to a Strong 2♣ Opening',
    'responding_to_2nt': 'Responding to 2NT Opening',
    'simple_raises': 'Simple Raises (Supporting Partner)',

    // Level 3+: Conventions
    'stayman': 'Stayman Convention',
    'jacoby_transfer': 'Jacoby Transfers',
    'blackwood': 'Blackwood Convention (Ace-Asking)',

    // === PLAY SKILLS ===
    // Level 0: Foundations
    'counting_winners': 'Counting Winners',
    'counting_losers': 'Counting Losers',
    'analyzing_the_lead': 'Analyzing the Lead',

    // Level 1: Basic Techniques
    'leading_to_tricks': 'Leading to Tricks',
    'second_hand_play': 'Second Hand Play',
    'third_hand_play': 'Third Hand Play',
    'ducking': 'Ducking',

    // Level 2: Finessing
    'simple_finesse': 'Simple Finesse',
    'double_finesse': 'Double Finesse',
    'finesse_or_drop': 'Finesse or Drop',
    'two_way_finesse': 'Two-Way Finesse',

    // Level 3: Suit Establishment
    'establishing_long_suits': 'Establishing Long Suits',
    'ducking_to_establish': 'Ducking to Establish',
    'counting_tricks_needed': 'Counting Tricks Needed',
    'timing_suit_establishment': 'Timing Suit Establishment',

    // Level 4: Trump Management
    'drawing_trumps': 'Drawing Trumps',
    'when_not_to_draw': 'When Not to Draw Trumps',
    'ruffing_losers': 'Ruffing Losers',
    'crossruff': 'Crossruff',

    // Level 5: Entry Management
    'preserving_entries': 'Preserving Entries',
    'creating_entries': 'Creating Entries',
    'using_dummy_entries': 'Using Dummy Entries',
    'entry_killing_plays': 'Entry-Killing Plays',

    // Level 6: Card Combinations
    'safety_plays': 'Safety Plays',
    'percentage_plays': 'Percentage Plays',
    'restricted_choice': 'Restricted Choice',
    'suit_combinations': 'Suit Combinations',

    // Level 7: Timing & Planning
    'planning_the_play': 'Planning the Play',
    'danger_hand': 'The Danger Hand',
    'avoidance_plays': 'Avoidance Plays',
    'hold_up_plays': 'Hold-Up Plays',

    // Level 8: Advanced Techniques
    'squeeze_basics': 'Squeeze Basics',
    'endplays': 'Endplays',
    'throw_in': 'Throw-In Plays',
    'loser_on_loser': 'Loser-on-Loser',
    'trump_coup': 'Trump Coup',
  };

  // Return explicit name if available, otherwise format the ID
  if (skillNames[skillId]) {
    return skillNames[skillId];
  }

  // Fallback: convert underscores to spaces and capitalize
  return skillId
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Question Prompt Component
 */
const QuestionPrompt = ({ questionType, expected, situation }) => {
  const getPrompt = () => {
    // Play skills - use the question from situation
    if (situation?.question) {
      return situation.question;
    }

    switch (questionType) {
      // Bidding skill types
      case 'hcp':
        return 'How many High Card Points (HCP) does this hand have?';
      case 'should_open':
        return 'Should you open this hand?';
      case 'bidding':
        // Check if partner opened (responding situation)
        if (expected?.partner_opened) {
          return `Partner opened ${expected.partner_opened}. What is your response?`;
        }
        return 'What would you bid with this hand?';
      case 'longest_suit':
        return 'What is the longest suit in this hand?';
      case 'game_points':
        return 'How many combined points do you need with partner to bid game?';
      case 'contract_points':
        // Contract-specific question
        const contract = expected?.display_contract || expected?.contract || 'game';
        return `How many combined points do you need to bid ${contract}?`;

      // Play skill types
      case 'count_winners':
        return 'How many sure tricks do you have in this contract?';
      case 'count_losers':
        return 'How many losers do you have in this hand?';
      case 'analyze_lead':
        return 'What does the opening lead tell you?';
      case 'finesse_direction':
        return 'Which direction should you finesse?';
      case 'finesse_or_drop':
        return 'Should you finesse or play for the drop?';
      case 'establish_suit':
        return 'How many tricks can you establish in this suit?';
      case 'hold_up':
        return 'How many times should you hold up?';
      case 'draw_trumps':
        return 'How many rounds of trumps should you draw?';
      case 'ruff_losers':
        return 'How many losers can you ruff in dummy?';
      case 'play_numeric':
        return 'Enter your answer:';

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
const AnswerInput = ({ questionType, expected, value, onChange, disabled }) => {
  // Normalize bid format for comparison (convert Unicode to ASCII uppercase)
  const normalizeBid = (bid) => {
    if (!bid) return '';
    return bid
      .replace(/♠/g, 'S')
      .replace(/♥/g, 'H')
      .replace(/♦/g, 'D')
      .replace(/♣/g, 'C')
      .toUpperCase();
  };

  // Get suit color class from bid
  const getSuitColorClass = (bid) => {
    if (!bid) return '';
    const normalized = normalizeBid(bid);
    if (normalized.includes('S')) return 'suit-spade';
    if (normalized.includes('H')) return 'suit-heart';
    if (normalized.includes('D')) return 'suit-diamond';
    if (normalized.includes('C') && !normalized.includes('NT')) return 'suit-club';
    return '';
  };

  // Determine which bid shortcuts to show based on context
  // Only shows LEGAL bids based on the auction
  const getBidShortcuts = () => {
    let shortcuts = [];

    // If responding to partner's opening, show only legal response bids
    if (expected?.partner_opened) {
      const opening = normalizeBid(expected.partner_opened);

      // After 1H: Can bid 1S (higher suit at same level), 1NT, or 2+ level
      if (opening === '1H') {
        shortcuts = [
          { bid: '1S', color: 'suit-spade' },
          { bid: '1NT', color: '' },
          { bid: '2C', color: 'suit-club' },
          { bid: '2D', color: 'suit-diamond' },
          { bid: '2H', color: 'suit-heart' },
          { bid: '2NT', color: '' },
          { bid: '3H', color: 'suit-heart' },
          { bid: '3NT', color: '' },
          { bid: '4H', color: 'suit-heart' },
          { bid: 'Pass', color: '' },
        ];
      }
      // After 1S: Cannot bid any 1-level suit, only 1NT or 2+ level
      else if (opening === '1S') {
        shortcuts = [
          { bid: '1NT', color: '' },
          { bid: '2C', color: 'suit-club' },
          { bid: '2D', color: 'suit-diamond' },
          { bid: '2H', color: 'suit-heart' },
          { bid: '2S', color: 'suit-spade' },
          { bid: '2NT', color: '' },
          { bid: '3S', color: 'suit-spade' },
          { bid: '3NT', color: '' },
          { bid: '4S', color: 'suit-spade' },
          { bid: 'Pass', color: '' },
        ];
      }
      // After 1C: Can bid 1D, 1H, 1S, 1NT, or higher
      else if (opening === '1C') {
        shortcuts = [
          { bid: '1D', color: 'suit-diamond' },
          { bid: '1H', color: 'suit-heart' },
          { bid: '1S', color: 'suit-spade' },
          { bid: '1NT', color: '' },
          { bid: '2C', color: 'suit-club' },
          { bid: '2NT', color: '' },
          { bid: '3C', color: 'suit-club' },
          { bid: '3NT', color: '' },
          { bid: 'Pass', color: '' },
        ];
      }
      // After 1D: Can bid 1H, 1S, 1NT, or higher
      else if (opening === '1D') {
        shortcuts = [
          { bid: '1H', color: 'suit-heart' },
          { bid: '1S', color: 'suit-spade' },
          { bid: '1NT', color: '' },
          { bid: '2C', color: 'suit-club' },
          { bid: '2D', color: 'suit-diamond' },
          { bid: '2NT', color: '' },
          { bid: '3D', color: 'suit-diamond' },
          { bid: '3NT', color: '' },
          { bid: 'Pass', color: '' },
        ];
      }
      // After 1NT: Stayman, transfers, or NT raises
      // Include 2S as a "trap" - legal but wrong when you should transfer
      else if (opening === '1NT') {
        shortcuts = [
          { bid: '2C', color: 'suit-club' },   // Stayman
          { bid: '2D', color: 'suit-diamond' }, // Transfer to hearts
          { bid: '2H', color: 'suit-heart' },   // Transfer to spades
          { bid: '2S', color: 'suit-spade' },   // Common mistake - should transfer instead
          { bid: '2NT', color: '' },            // Invitational (8-9 pts)
          { bid: '3NT', color: '' },            // Game (10-15 pts)
          { bid: '4H', color: 'suit-heart' },   // To play (6+ hearts, game values)
          { bid: '4S', color: 'suit-spade' },   // To play (6+ spades, game values)
          { bid: 'Pass', color: '' },           // Weak (0-7 pts)
        ];
      }
      // After 2C (strong): Game-forcing, cannot pass!
      // Must respond at 2-level or higher
      // Include Pass as a "trap" - users may forget 2C is forcing!
      else if (opening === '2C') {
        shortcuts = [
          { bid: '2D', color: 'suit-diamond' },  // Waiting bid (artificial, 0-7 HCP)
          { bid: '2H', color: 'suit-heart' },    // Positive, 5+ hearts with 2 of top 3
          { bid: '2S', color: 'suit-spade' },    // Positive, 5+ spades with 2 of top 3
          { bid: '2NT', color: '' },             // Positive, 8+ HCP balanced
          { bid: '3C', color: 'suit-club' },     // Positive, 5+ clubs with 2 of top 3
          { bid: '3D', color: 'suit-diamond' },  // Positive, 5+ diamonds with 2 of top 3
          { bid: 'Pass', color: '' },            // TRAP! 2C is game-forcing - cannot pass!
        ];
      }
      // After 2NT (20-21 HCP): Similar to 1NT responses but at 3-level
      // Include 3S as a "trap" - legal but wrong when you should transfer
      else if (opening === '2NT') {
        shortcuts = [
          { bid: '3C', color: 'suit-club' },    // Stayman
          { bid: '3D', color: 'suit-diamond' }, // Transfer to hearts
          { bid: '3H', color: 'suit-heart' },   // Transfer to spades
          { bid: '3S', color: 'suit-spade' },   // Common mistake - should transfer instead
          { bid: '3NT', color: '' },            // To play (5+ pts)
          { bid: '4H', color: 'suit-heart' },   // To play (6+ hearts)
          { bid: '4S', color: 'suit-spade' },   // To play (6+ spades)
          { bid: 'Pass', color: '' },           // Weak (0-4 pts)
        ];
      }
    }

    // Default opening bid shortcuts (no prior bids)
    if (shortcuts.length === 0) {
      shortcuts = [
        { bid: '1C', color: 'suit-club' },
        { bid: '1D', color: 'suit-diamond' },
        { bid: '1H', color: 'suit-heart' },
        { bid: '1S', color: 'suit-spade' },
        { bid: '1NT', color: '' },
        { bid: '2C', color: 'suit-club' },
        { bid: '2NT', color: '' },
        { bid: 'Pass', color: '' },
      ];
    }

    // Ensure the correct answer is in the shortcuts (if we know it)
    if (expected?.bid) {
      const correctBid = normalizeBid(expected.bid);
      const hasCorrectBid = shortcuts.some(s => normalizeBid(s.bid) === correctBid);
      if (!hasCorrectBid && correctBid !== 'PASS') {
        // Add the correct answer to the shortcuts
        shortcuts.push({
          bid: correctBid,
          color: getSuitColorClass(correctBid),
        });
      }
    }

    return shortcuts;
  };

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
            {getBidShortcuts().map(({ bid, color }) => (
              <button
                key={bid}
                type="button"
                className={`bid-shortcut ${color} ${value === bid ? 'selected' : ''}`}
                onClick={() => onChange(bid)}
                disabled={disabled}
              >
                {formatBid(bid)}
              </button>
            ))}
          </div>
        </div>
      );

    case 'longest_suit':
      return (
        <div className="suit-buttons">
          {[
            { suit: '♠', label: 'Spades', value: '♠' },
            { suit: '♥', label: 'Hearts', value: '♥' },
            { suit: '♦', label: 'Diamonds', value: '♦' },
            { suit: '♣', label: 'Clubs', value: '♣' },
          ].map(({ suit, label, value: suitValue }) => (
            <button
              key={suit}
              type="button"
              className={`suit-button ${value === suitValue ? 'selected' : ''} ${suit === '♥' || suit === '♦' ? 'red' : 'black'}`}
              onClick={() => onChange(suitValue)}
              disabled={disabled}
            >
              <span className="suit-symbol">{suit}</span>
              <span className="suit-name">{label}</span>
            </button>
          ))}
        </div>
      );

    case 'game_points':
      return (
        <div className="points-buttons">
          {[20, 23, 25, 26, 28, 30].map((pts) => (
            <button
              key={pts}
              type="button"
              className={`points-button ${value === String(pts) ? 'selected' : ''}`}
              onClick={() => onChange(String(pts))}
              disabled={disabled}
            >
              {pts}
            </button>
          ))}
        </div>
      );

    case 'contract_points':
      // Contract-specific points - show relevant options
      return (
        <div className="points-buttons">
          {[25, 29, 33, 37].map((pts) => (
            <button
              key={pts}
              type="button"
              className={`points-button ${value === String(pts) ? 'selected' : ''}`}
              onClick={() => onChange(String(pts))}
              disabled={disabled}
            >
              {pts}
            </button>
          ))}
        </div>
      );

    // Play skill types - most use numeric input
    case 'count_winners':
    case 'count_losers':
    case 'establish_suit':
    case 'hold_up':
    case 'draw_trumps':
    case 'ruff_losers':
    case 'play_numeric':
      return (
        <div className="play-answer-area">
          <input
            type="number"
            className="answer-input play-number-input"
            placeholder="Enter number"
            min="0"
            max="13"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            autoFocus
          />
          <div className="number-shortcuts">
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map((num) => (
              <button
                key={num}
                type="button"
                className={`number-shortcut ${value === String(num) ? 'selected' : ''}`}
                onClick={() => onChange(String(num))}
                disabled={disabled}
              >
                {num}
              </button>
            ))}
          </div>
        </div>
      );

    case 'finesse_direction':
      return (
        <div className="direction-buttons">
          <button
            type="button"
            className={`direction-button ${value === 'toward_dummy' ? 'selected' : ''}`}
            onClick={() => onChange('toward_dummy')}
            disabled={disabled}
          >
            Lead toward Dummy
          </button>
          <button
            type="button"
            className={`direction-button ${value === 'toward_hand' ? 'selected' : ''}`}
            onClick={() => onChange('toward_hand')}
            disabled={disabled}
          >
            Lead toward Hand
          </button>
        </div>
      );

    case 'finesse_or_drop':
      return (
        <div className="choice-buttons">
          <button
            type="button"
            className={`choice-button ${value === 'finesse' ? 'selected' : ''}`}
            onClick={() => onChange('finesse')}
            disabled={disabled}
          >
            Finesse
          </button>
          <button
            type="button"
            className={`choice-button ${value === 'drop' ? 'selected' : ''}`}
            onClick={() => onChange('drop')}
            disabled={disabled}
          >
            Play for the Drop
          </button>
        </div>
      );

    case 'analyze_lead':
      return (
        <input
          type="text"
          className="answer-input"
          placeholder="Describe the lead..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          autoFocus
        />
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
 * Handles special bids (Pass, X, XX) and converts suit letters to symbols
 */
const formatBid = (bid) => {
  if (!bid) return bid;

  // Handle special bids that shouldn't have letter replacements
  const upperBid = bid.toUpperCase();
  if (upperBid === 'PASS') return 'Pass';
  if (upperBid === 'X' || upperBid === 'DOUBLE') return 'X';
  if (upperBid === 'XX' || upperBid === 'REDOUBLE') return 'XX';

  // For regular bids, only replace suit letters that follow a number
  // This handles bids like "1C", "2NT", "3S" etc.
  return bid
    .replace(/(\d)C/gi, '$1♣')
    .replace(/(\d)D/gi, '$1♦')
    .replace(/(\d)H/gi, '$1♥')
    .replace(/(\d)S/gi, '$1♠');
};

/**
 * Feedback Display Component
 */
const FeedbackDisplay = ({ result, expected, onContinue, onReplay, isReviewing, isReplaying, canContinue }) => {
  if (!result) return null;

  const { isCorrect, feedback } = result;

  return (
    <div className={`feedback-display ${isCorrect ? 'correct' : 'incorrect'} ${isReviewing ? 'reviewing' : ''}`}>
      {isReviewing && (
        <div className="reviewing-badge">Reviewing</div>
      )}
      <div className="feedback-icon">
        {isCorrect ? '✓' : '✗'}
      </div>
      <div className="feedback-content">
        <h4>{isCorrect ? 'Correct!' : 'Not quite...'}</h4>
        <p className="feedback-text">
          <TermHighlight text={feedback || ''} />
        </p>
        {expected?.explanation && !isCorrect && (
          <p className="explanation">
            <TermHighlight text={expected.explanation} />
          </p>
        )}
      </div>
      <div className="feedback-actions">
        <button onClick={onReplay} className="replay-button">
          {isReplaying ? 'Try Again' : 'Replay Hand'}
        </button>
        {canContinue && (
          <button onClick={onContinue} className="continue-button">
            Continue
          </button>
        )}
      </div>
      {isReviewing && !canContinue && (
        <p className="review-hint">Use the hand navigation above to view other hands</p>
      )}
    </div>
  );
};

export default SkillPractice;
