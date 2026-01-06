/**
 * HeuristicScorecard Component - Physics-Based Play Feedback
 *
 * Maps DDS signal heuristics to human-understandable "Physics Principles" of bridge:
 *
 * 1. CONSERVATION - Don't waste high honors (Ace-on-King prevention)
 * 2. FLUIDITY - Keep suit unblocked for partner runs
 * 3. SIGNALING - Honest card choices for partner trust
 * 4. RESOURCES - Maintain HCP floors and entry preservation
 *
 * This component replaces "No detailed analysis" with educational diagnostics
 * that explain WHY a card choice matters strategically.
 *
 * V3 Architecture Layer: UI Rendering (4th tier)
 * Consumes: signal_reason, signal_heuristic, signal_context from backend
 * Produces: Human-readable principle badges and comparison tables
 */

import React from 'react';
import PropTypes from 'prop-types';

// Physics Principles mapping from signal heuristics
const PHYSICS_PRINCIPLES = {
  // CONSERVATION - Preserve high cards
  DECLARER_CONSERVE: {
    principle: 'Conservation',
    icon: '💎',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Preserve high cards for future tricks'
  },
  DEFENSIVE_DEFER: {
    principle: 'Conservation',
    icon: '💎',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: "Don't overtake partner's winner"
  },
  MIN_OF_EQUALS: {
    principle: 'Conservation',
    icon: '💎',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Save higher cards for later rounds'
  },
  CHEAPEST_WINNER: {
    principle: 'Conservation',
    icon: '💎',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Win with lowest necessary card'
  },
  PROTECT_STOPPERS: {
    principle: 'Conservation',
    icon: '💎',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Keep cards that guard suits'
  },

  // FLUIDITY - Unblock suits
  BOTTOM_OF_SEQUENCE: {
    principle: 'Fluidity',
    icon: '🌊',
    color: '#3b82f6',
    bgColor: '#eff6ff',
    description: 'Unblock to let partner run the suit'
  },
  DISCARD_FROM_LENGTH: {
    principle: 'Fluidity',
    icon: '🌊',
    color: '#3b82f6',
    bgColor: '#eff6ff',
    description: 'Clear blocked suits'
  },

  // SIGNALING - Partner communication
  TOP_OF_SEQUENCE: {
    principle: 'Signaling',
    icon: '📡',
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    description: 'Promises touching honors below'
  },
  ATTITUDE_SIGNAL: {
    principle: 'Signaling',
    icon: '📡',
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    description: 'High encourages, low discourages'
  },
  COUNT_SIGNAL: {
    principle: 'Signaling',
    icon: '📡',
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    description: 'High-low = even count'
  },

  // RESOURCES - Maximize trick potential
  MAX_OF_EQUALS: {
    principle: 'Resources',
    icon: '⚡',
    color: '#f59e0b',
    bgColor: '#fffbeb',
    description: 'Force out opponent high cards'
  }
};

// Default principle for unknown heuristics
const DEFAULT_PRINCIPLE = {
  principle: 'Tactical',
  icon: '🎯',
  color: '#6b7280',
  bgColor: '#f9fafb',
  description: 'Standard play technique'
};

/**
 * Get physics principle mapping for a signal heuristic
 */
const getPrincipleMapping = (heuristic) => {
  if (!heuristic) return null;
  // Handle both "MIN_OF_EQUALS" and "min_of_equals" formats
  const normalized = heuristic.toUpperCase().replace(/-/g, '_');
  return PHYSICS_PRINCIPLES[normalized] || DEFAULT_PRINCIPLE;
};

/**
 * PrincipleBadge - Shows a single physics principle with icon
 */
const PrincipleBadge = ({ principle, isOptimal = true }) => {
  if (!principle) return null;

  const { icon, color, bgColor, principle: name, description } = principle;

  return (
    <div
      className="principle-badge"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '4px 8px',
        borderRadius: '6px',
        backgroundColor: isOptimal ? bgColor : '#fef2f2',
        border: `1px solid ${isOptimal ? color : '#dc2626'}`,
        fontSize: '0.75rem',
        fontWeight: 500
      }}
      title={description}
      data-testid="principle-badge"
    >
      <span style={{ fontSize: '0.875rem' }}>{icon}</span>
      <span style={{ color: isOptimal ? color : '#dc2626' }}>{name}</span>
    </div>
  );
};

/**
 * StrategicDiagnostic - Shows the physics principle and explanation
 */
const StrategicDiagnostic = ({ signalReason, signalHeuristic, isSignalOptimal }) => {
  const principle = getPrincipleMapping(signalHeuristic);

  if (!signalReason && !principle) {
    return null;
  }

  return (
    <div
      className="strategic-diagnostic"
      style={{
        marginTop: '12px',
        padding: '10px 12px',
        backgroundColor: isSignalOptimal ? '#f0fdf4' : '#fef2f2',
        border: `1px solid ${isSignalOptimal ? '#86efac' : '#fecaca'}`,
        borderRadius: '8px'
      }}
      data-testid="strategic-diagnostic"
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: signalReason ? '8px' : '0'
      }}>
        <span style={{
          fontSize: '0.7rem',
          fontWeight: 600,
          color: '#6b7280',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Principle Applied:
        </span>
        {principle && <PrincipleBadge principle={principle} isOptimal={isSignalOptimal} />}
      </div>

      {signalReason && (
        <p style={{
          margin: 0,
          fontSize: '0.875rem',
          color: '#374151',
          lineHeight: '1.4'
        }}>
          {signalReason}
        </p>
      )}
    </div>
  );
};

/**
 * DeductionComparison - Shows what partner infers from user's play vs optimal
 *
 * This helps users understand the information theory of card selection:
 * different cards send different messages to partner.
 */
const DeductionComparison = ({
  userCard,
  optimalCard,
  signalHeuristic,
  signalContext,
  isSignalOptimal
}) => {
  // Only show comparison when user didn't play optimally
  if (isSignalOptimal || !optimalCard || userCard === optimalCard) {
    return null;
  }

  const principle = getPrincipleMapping(signalHeuristic);

  // Generate inference descriptions based on context
  const getInferenceDescription = (card, isOptimal) => {
    if (!signalContext) return 'Standard play';

    const context = signalContext.toUpperCase();

    if (context.includes('SECOND_HAND')) {
      return isOptimal
        ? 'Preserves honor strength for later'
        : 'Wastes high card unnecessarily';
    }
    if (context.includes('THIRD_HAND')) {
      return isOptimal
        ? 'Forces declarer to commit resources'
        : 'Lets declarer win cheaply';
    }
    if (context.includes('FOURTH_HAND')) {
      return isOptimal
        ? 'Wins trick efficiently'
        : 'Overwins or underwins the trick';
    }
    if (context.includes('DISCARD')) {
      return isOptimal
        ? 'Sends clear signal to partner'
        : 'Confusing or wasteful discard';
    }
    if (context.includes('CONSERVATION') || context.includes('DEFER')) {
      return isOptimal
        ? 'Keeps winners for future tricks'
        : 'Wastes winner on already-won trick';
    }
    if (context.includes('SEQUENCE')) {
      return isOptimal
        ? 'Signals touching honors'
        : 'Misleads partner about honor holding';
    }

    return isOptimal ? 'Follows bridge conventions' : 'Deviates from standard play';
  };

  return (
    <div
      className="deduction-comparison"
      style={{
        marginTop: '12px',
        padding: '10px 12px',
        backgroundColor: '#fffbeb',
        border: '1px solid #fcd34d',
        borderRadius: '8px'
      }}
      data-testid="deduction-comparison"
    >
      <div style={{
        fontSize: '0.7rem',
        fontWeight: 600,
        color: '#92400e',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        marginBottom: '8px'
      }}>
        Inference Shift
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        fontSize: '0.8rem'
      }}>
        {/* Your Play */}
        <div>
          <div style={{
            fontWeight: 600,
            color: '#dc2626',
            marginBottom: '2px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <span>✗</span> You played: {userCard}
          </div>
          <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>
            {getInferenceDescription(userCard, false)}
          </div>
        </div>

        {/* Expert Play */}
        <div>
          <div style={{
            fontWeight: 600,
            color: '#059669',
            marginBottom: '2px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <span>✓</span> Better: {optimalCard}
          </div>
          <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>
            {getInferenceDescription(optimalCard, true)}
          </div>
        </div>
      </div>

      {principle && (
        <div style={{
          marginTop: '8px',
          paddingTop: '8px',
          borderTop: '1px solid #fcd34d',
          fontSize: '0.75rem',
          color: '#78716c'
        }}>
          <strong>Principle violated:</strong> {principle.principle} - {principle.description}
        </div>
      )}
    </div>
  );
};

/**
 * HeuristicScorecard - Main component combining all diagnostics
 *
 * Displays:
 * 1. Strategic Diagnostic with physics principle badge
 * 2. Deduction Comparison table (when play differs from optimal)
 *
 * Props:
 * - decision: PlayFeedback object from backend with signal_* fields
 */
const HeuristicScorecard = ({ decision }) => {
  if (!decision) return null;

  const {
    signal_reason: signalReason,
    signal_heuristic: signalHeuristic,
    signal_context: signalContext,
    is_signal_optimal: isSignalOptimal,
    user_card: userCard,
    optimal_card: optimalCard
  } = decision;

  // Nothing to show if no signal analysis available
  if (!signalReason && !signalHeuristic) {
    return null;
  }

  return (
    <div
      className="heuristic-scorecard"
      data-testid="heuristic-scorecard"
    >
      <StrategicDiagnostic
        signalReason={signalReason}
        signalHeuristic={signalHeuristic}
        isSignalOptimal={isSignalOptimal}
      />

      <DeductionComparison
        userCard={userCard}
        optimalCard={optimalCard}
        signalHeuristic={signalHeuristic}
        signalContext={signalContext}
        isSignalOptimal={isSignalOptimal}
      />
    </div>
  );
};

HeuristicScorecard.propTypes = {
  decision: PropTypes.shape({
    signal_reason: PropTypes.string,
    signal_heuristic: PropTypes.string,
    signal_context: PropTypes.string,
    is_signal_optimal: PropTypes.bool,
    user_card: PropTypes.string,
    optimal_card: PropTypes.string
  })
};

export default HeuristicScorecard;

// Also export sub-components for testing
export {
  PrincipleBadge,
  StrategicDiagnostic,
  DeductionComparison,
  getPrincipleMapping,
  PHYSICS_PRINCIPLES
};
