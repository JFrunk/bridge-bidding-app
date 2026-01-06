/**
 * BiddingGovernorPanel Component - Physics-Based Bidding Feedback
 *
 * Maps bidding errors and governors to human-understandable "Physics Principles" of bridge:
 *
 * 1. RESOURCES - HCP floors and combined point requirements
 * 2. SHAPE - Distributional requirements (Rule of 20, suit lengths)
 * 3. SAFETY - Level-appropriate bidding (don't overbid the hand)
 * 4. COMMUNICATION - Partnership agreements and forcing bids
 *
 * This component provides educational diagnostics for bidding decisions,
 * explaining WHY a bid was flagged by the various safety governors.
 *
 * V3 Architecture Layer: UI Rendering (4th tier)
 * Consumes: bidding_quality_summary from hand-detail API
 * Produces: Human-readable principle badges and governor explanations
 */

import React from 'react';
import PropTypes from 'prop-types';

// Physics Principles for Bidding - mapped from error categories and governors
const BIDDING_PRINCIPLES = {
  // RESOURCES - HCP and point requirements
  HCP_FLOOR: {
    principle: 'Resources',
    icon: '💰',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Minimum HCP required for the bid level'
  },
  STRENGTH_OVERVALUE: {
    principle: 'Resources',
    icon: '💰',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Hand strength was overvalued'
  },
  STRENGTH_UNDERVALUE: {
    principle: 'Resources',
    icon: '💰',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Hand strength was undervalued'
  },
  COMBINED_POINTS: {
    principle: 'Resources',
    icon: '💰',
    color: '#059669',
    bgColor: '#ecfdf5',
    description: 'Partnership combined point total'
  },

  // SHAPE - Distributional requirements
  RULE_OF_20: {
    principle: 'Shape',
    icon: '📐',
    color: '#3b82f6',
    bgColor: '#eff6ff',
    description: 'HCP + two longest suits must equal 20+ to open'
  },
  SUIT_LENGTH: {
    principle: 'Shape',
    icon: '📐',
    color: '#3b82f6',
    bgColor: '#eff6ff',
    description: 'Suit length requirement not met'
  },
  DISTRIBUTION: {
    principle: 'Shape',
    icon: '📐',
    color: '#3b82f6',
    bgColor: '#eff6ff',
    description: 'Hand shape affects bid choice'
  },
  BALANCED_SHAPE: {
    principle: 'Shape',
    icon: '📐',
    color: '#3b82f6',
    bgColor: '#eff6ff',
    description: 'Balanced vs unbalanced hand evaluation'
  },

  // SAFETY - Level-appropriate bidding
  LEVEL_TOO_HIGH: {
    principle: 'Safety',
    icon: '🛡️',
    color: '#dc2626',
    bgColor: '#fef2f2',
    description: 'Bid level exceeds hand strength'
  },
  LEVEL_TOO_LOW: {
    principle: 'Safety',
    icon: '🛡️',
    color: '#f59e0b',
    bgColor: '#fffbeb',
    description: 'Bid level undervalues hand strength'
  },
  SLAM_SAFETY: {
    principle: 'Safety',
    icon: '🛡️',
    color: '#dc2626',
    bgColor: '#fef2f2',
    description: 'Slam requires 33+ combined points'
  },
  GRAND_SLAM_SAFETY: {
    principle: 'Safety',
    icon: '🛡️',
    color: '#dc2626',
    bgColor: '#fef2f2',
    description: 'Grand slam requires all aces and 37+ points'
  },
  COMPETITIVE_SAFETY: {
    principle: 'Safety',
    icon: '🛡️',
    color: '#f59e0b',
    bgColor: '#fffbeb',
    description: 'Competitive bidding level requirements'
  },

  // COMMUNICATION - Partnership agreements
  FORCING_BID: {
    principle: 'Communication',
    icon: '📡',
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    description: 'Forcing bid requires a response'
  },
  BLACKWOOD: {
    principle: 'Communication',
    icon: '📡',
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    description: 'Use 4NT to ask for aces before slam'
  },
  CONVENTION_MEANING: {
    principle: 'Communication',
    icon: '📡',
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    description: 'Convention bid has specific meaning'
  },
  SUPPORT_SIGNAL: {
    principle: 'Communication',
    icon: '📡',
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    description: 'Show support for partner\'s suit'
  }
};

// Default principle for unknown categories
const DEFAULT_PRINCIPLE = {
  principle: 'Judgment',
  icon: '🎯',
  color: '#6b7280',
  bgColor: '#f9fafb',
  description: 'Standard bidding judgment'
};

/**
 * Map error category and correctness to a physics principle
 */
const mapToPhysicsPrinciple = (decision) => {
  const { correctness, impact, helpful_hint } = decision;
  const hint = (helpful_hint || '').toLowerCase();

  // Slam bidding errors
  if (hint.includes('slam') || hint.includes('blackwood')) {
    if (hint.includes('4nt') || hint.includes('blackwood')) {
      return BIDDING_PRINCIPLES.BLACKWOOD;
    }
    if (hint.includes('grand')) {
      return BIDDING_PRINCIPLES.GRAND_SLAM_SAFETY;
    }
    return BIDDING_PRINCIPLES.SLAM_SAFETY;
  }

  // HCP and point-based errors
  if (hint.includes('hcp') || hint.includes('points')) {
    if (hint.includes('overvalue') || hint.includes('overbid')) {
      return BIDDING_PRINCIPLES.STRENGTH_OVERVALUE;
    }
    if (hint.includes('undervalue') || hint.includes('enough for')) {
      return BIDDING_PRINCIPLES.STRENGTH_UNDERVALUE;
    }
    if (hint.includes('combined')) {
      return BIDDING_PRINCIPLES.COMBINED_POINTS;
    }
    return BIDDING_PRINCIPLES.HCP_FLOOR;
  }

  // Shape-based errors
  if (hint.includes('shape') || hint.includes('balanced') || hint.includes('unbalanced')) {
    return BIDDING_PRINCIPLES.BALANCED_SHAPE;
  }
  if (hint.includes('suit') && (hint.includes('longest') || hint.includes('length') || hint.includes('cards'))) {
    return BIDDING_PRINCIPLES.SUIT_LENGTH;
  }
  if (hint.includes('distribution') || hint.includes('total points')) {
    return BIDDING_PRINCIPLES.DISTRIBUTION;
  }
  if (hint.includes('rule of 20')) {
    return BIDDING_PRINCIPLES.RULE_OF_20;
  }

  // Level errors
  if (impact === 'critical' || impact === 'significant') {
    if (hint.includes('too high') || hint.includes('higher level')) {
      return BIDDING_PRINCIPLES.LEVEL_TOO_HIGH;
    }
    if (hint.includes('too low') || hint.includes('lower level')) {
      return BIDDING_PRINCIPLES.LEVEL_TOO_LOW;
    }
  }

  // Communication/convention errors
  if (hint.includes('support') || hint.includes('fit')) {
    return BIDDING_PRINCIPLES.SUPPORT_SIGNAL;
  }
  if (hint.includes('convention') || hint.includes('meaning')) {
    return BIDDING_PRINCIPLES.CONVENTION_MEANING;
  }
  if (hint.includes('forcing')) {
    return BIDDING_PRINCIPLES.FORCING_BID;
  }

  // Competitive bidding
  if (hint.includes('competitive') || hint.includes('overcall') || hint.includes('double')) {
    return BIDDING_PRINCIPLES.COMPETITIVE_SAFETY;
  }

  // Default based on correctness
  if (correctness === 'error') {
    return BIDDING_PRINCIPLES.LEVEL_TOO_HIGH;
  }
  if (correctness === 'suboptimal') {
    return BIDDING_PRINCIPLES.HCP_FLOOR;
  }

  return DEFAULT_PRINCIPLE;
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
      data-testid="bidding-principle-badge"
    >
      <span style={{ fontSize: '0.875rem' }}>{icon}</span>
      <span style={{ color: isOptimal ? color : '#dc2626' }}>{name}</span>
    </div>
  );
};

/**
 * GovernorExplanation - Explains why a bid was flagged
 */
const GovernorExplanation = ({ decision, principle }) => {
  const { user_bid, optimal_bid, helpful_hint, correctness, impact } = decision;
  const isOptimal = correctness === 'optimal';

  // Don't show for optimal bids
  if (isOptimal) {
    return null;
  }

  return (
    <div
      className="governor-explanation"
      style={{
        marginTop: '8px',
        padding: '10px 12px',
        backgroundColor: isOptimal ? '#f0fdf4' : '#fef2f2',
        border: `1px solid ${isOptimal ? '#86efac' : '#fecaca'}`,
        borderRadius: '8px'
      }}
      data-testid="governor-explanation"
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '8px'
      }}>
        <span style={{
          fontSize: '0.7rem',
          fontWeight: 600,
          color: '#6b7280',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Governor Applied:
        </span>
        <PrincipleBadge principle={principle} isOptimal={false} />
        {impact && impact !== 'none' && (
          <span style={{
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '0.7rem',
            fontWeight: 500,
            backgroundColor: impact === 'critical' ? '#dc2626' :
                           impact === 'significant' ? '#f59e0b' : '#6b7280',
            color: 'white'
          }}>
            {impact}
          </span>
        )}
      </div>

      {helpful_hint && (
        <p style={{
          margin: 0,
          fontSize: '0.875rem',
          color: '#374151',
          lineHeight: '1.4'
        }}>
          {helpful_hint}
        </p>
      )}
    </div>
  );
};

/**
 * BidComparison - Shows user's bid vs optimal bid
 */
const BidComparison = ({ decision }) => {
  const { user_bid, optimal_bid, correctness } = decision;
  const isCorrect = correctness === 'optimal' || correctness === 'acceptable';

  // Don't show comparison for optimal bids
  if (user_bid === optimal_bid) {
    return null;
  }

  return (
    <div
      className="bid-comparison"
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        marginTop: '8px',
        padding: '8px 12px',
        backgroundColor: '#fffbeb',
        border: '1px solid #fcd34d',
        borderRadius: '8px',
        fontSize: '0.8rem'
      }}
      data-testid="bid-comparison"
    >
      {/* Your Bid */}
      <div>
        <div style={{
          fontWeight: 600,
          color: isCorrect ? '#059669' : '#dc2626',
          marginBottom: '2px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <span>{isCorrect ? '○' : '✗'}</span> You bid: {user_bid}
        </div>
        <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>
          {correctness === 'optimal' ? 'Perfect choice!' :
           correctness === 'acceptable' ? 'Reasonable alternative' :
           correctness === 'suboptimal' ? 'Works but not ideal' :
           'Significant error'}
        </div>
      </div>

      {/* Better Bid */}
      <div>
        <div style={{
          fontWeight: 600,
          color: '#059669',
          marginBottom: '2px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <span>✓</span> Better: {optimal_bid}
        </div>
        <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>
          Optimal choice for this hand
        </div>
      </div>
    </div>
  );
};

/**
 * BiddingDecisionCard - Individual bidding decision display
 */
const BiddingDecisionCard = ({ decision, index }) => {
  const { user_bid, optimal_bid, score, correctness, position, bid_number } = decision;
  const principle = mapToPhysicsPrinciple(decision);
  const isOptimal = correctness === 'optimal';
  const isAcceptable = correctness === 'acceptable';
  const isGood = isOptimal || isAcceptable;

  // Correctness badge config
  const badgeConfig = {
    optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '✓', label: 'Optimal' },
    acceptable: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Acceptable' },
    suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
    error: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Error' }
  };
  const config = badgeConfig[correctness] || badgeConfig.suboptimal;

  return (
    <div
      className="bidding-decision-card"
      style={{
        padding: '12px',
        marginBottom: '12px',
        border: `1px solid ${isGood ? '#e5e7eb' : '#fecaca'}`,
        borderRadius: '8px',
        backgroundColor: isGood ? '#ffffff' : '#fef2f2'
      }}
      data-testid="bidding-decision-card"
    >
      {/* Header row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontSize: '0.75rem',
            color: '#6b7280',
            fontWeight: 500
          }}>
            Bid #{bid_number} ({position})
          </span>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 500,
            backgroundColor: config.bgColor,
            color: config.color
          }}>
            {config.icon} {config.label}
          </span>
        </div>
        {score !== null && score !== undefined && (
          <span style={{
            fontSize: '0.875rem',
            fontWeight: 600,
            color: score >= 7 ? '#059669' : score >= 4 ? '#f59e0b' : '#dc2626'
          }}>
            {score}/10
          </span>
        )}
      </div>

      {/* Bid display */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '8px'
      }}>
        <span style={{
          fontSize: '1.25rem',
          fontWeight: 600,
          padding: '4px 12px',
          borderRadius: '6px',
          backgroundColor: isGood ? '#f0fdf4' : '#fef2f2',
          border: `2px solid ${isGood ? '#86efac' : '#fecaca'}`
        }}>
          {user_bid}
        </span>
        {!isOptimal && optimal_bid && optimal_bid !== user_bid && (
          <>
            <span style={{ color: '#9ca3af' }}>→</span>
            <span style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              padding: '4px 12px',
              borderRadius: '6px',
              backgroundColor: '#f0fdf4',
              border: '2px solid #86efac'
            }}>
              {optimal_bid}
            </span>
          </>
        )}
      </div>

      {/* Principle badge for non-optimal bids */}
      {!isOptimal && (
        <div style={{ marginBottom: '8px' }}>
          <PrincipleBadge principle={principle} isOptimal={false} />
        </div>
      )}

      {/* Governor explanation for errors */}
      {!isGood && (
        <GovernorExplanation decision={decision} principle={principle} />
      )}

      {/* Bid comparison for acceptable bids */}
      {isAcceptable && optimal_bid && optimal_bid !== user_bid && (
        <BidComparison decision={decision} />
      )}
    </div>
  );
};

/**
 * BiddingSummaryHeader - Summary statistics for the hand
 */
const BiddingSummaryHeader = ({ summary }) => {
  const {
    total_bids,
    optimal_count,
    acceptable_count,
    suboptimal_count,
    error_count,
    avg_score,
    accuracy_rate
  } = summary;

  const getGrade = (rate) => {
    if (rate >= 90) return { grade: 'A', color: '#059669' };
    if (rate >= 75) return { grade: 'B', color: '#3b82f6' };
    if (rate >= 60) return { grade: 'C', color: '#f59e0b' };
    return { grade: 'D', color: '#dc2626' };
  };

  const gradeInfo = getGrade(accuracy_rate);

  return (
    <div
      className="bidding-summary-header"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        marginBottom: '16px'
      }}
      data-testid="bidding-summary-header"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          fontSize: '2rem',
          fontWeight: 700,
          color: gradeInfo.color
        }}>
          {gradeInfo.grade}
        </div>
        <div>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#374151' }}>
            {accuracy_rate}% Accuracy
          </div>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
            {total_bids} bid{total_bids !== 1 ? 's' : ''} evaluated
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        {optimal_count > 0 && (
          <span style={{
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            backgroundColor: '#ecfdf5',
            color: '#059669'
          }}>
            {optimal_count} optimal
          </span>
        )}
        {acceptable_count > 0 && (
          <span style={{
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            backgroundColor: '#eff6ff',
            color: '#3b82f6'
          }}>
            {acceptable_count} acceptable
          </span>
        )}
        {(suboptimal_count > 0 || error_count > 0) && (
          <span style={{
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            backgroundColor: '#fef2f2',
            color: '#dc2626'
          }}>
            {suboptimal_count + error_count} to review
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * BiddingGovernorPanel - Main component for bidding feedback
 *
 * Displays physics-principle-based analysis of bidding decisions,
 * showing which "governors" were applied and why.
 */
const BiddingGovernorPanel = ({ biddingQualitySummary }) => {
  // Handle no data case
  if (!biddingQualitySummary || !biddingQualitySummary.has_data) {
    return (
      <div
        className="bidding-governor-panel no-data"
        style={{
          padding: '16px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          textAlign: 'center'
        }}
        data-testid="bidding-governor-panel-no-data"
      >
        <p style={{ margin: 0, color: '#6b7280' }}>
          No bidding analysis available for this hand
        </p>
        <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: '#9ca3af' }}>
          Bidding decisions are recorded when you submit bids during play
        </p>
      </div>
    );
  }

  const { all_decisions } = biddingQualitySummary;

  // Filter to show only user's bids (position S or relevant)
  const userDecisions = all_decisions || [];

  // If all decisions were optimal, show congratulations
  const allOptimal = userDecisions.every(d => d.correctness === 'optimal');

  return (
    <div
      className="bidding-governor-panel"
      style={{
        padding: '16px',
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}
      data-testid="bidding-governor-panel"
    >
      {/* Summary header */}
      <BiddingSummaryHeader summary={biddingQualitySummary} />

      {/* All optimal celebration */}
      {allOptimal && userDecisions.length > 0 && (
        <div
          style={{
            padding: '16px',
            backgroundColor: '#ecfdf5',
            border: '1px solid #86efac',
            borderRadius: '8px',
            textAlign: 'center',
            marginBottom: '16px'
          }}
          data-testid="all-optimal-celebration"
        >
          <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>
            Perfect Bidding!
          </div>
          <p style={{ margin: 0, color: '#059669' }}>
            All {userDecisions.length} bid{userDecisions.length !== 1 ? 's' : ''} were optimal.
            Your bidding governors are well-calibrated!
          </p>
        </div>
      )}

      {/* Individual decisions */}
      <div className="bidding-decisions-list">
        {userDecisions.map((decision, index) => (
          <BiddingDecisionCard
            key={decision.id || index}
            decision={decision}
            index={index}
          />
        ))}
      </div>

      {/* Physics principles legend */}
      <div
        className="principles-legend"
        style={{
          marginTop: '16px',
          padding: '12px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px'
        }}
      >
        <div style={{
          fontSize: '0.7rem',
          fontWeight: 600,
          color: '#6b7280',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '8px'
        }}>
          Bidding Principles
        </div>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          <PrincipleBadge principle={BIDDING_PRINCIPLES.HCP_FLOOR} isOptimal={true} />
          <PrincipleBadge principle={BIDDING_PRINCIPLES.RULE_OF_20} isOptimal={true} />
          <PrincipleBadge principle={BIDDING_PRINCIPLES.SLAM_SAFETY} isOptimal={true} />
          <PrincipleBadge principle={BIDDING_PRINCIPLES.CONVENTION_MEANING} isOptimal={true} />
        </div>
      </div>
    </div>
  );
};

BiddingGovernorPanel.propTypes = {
  biddingQualitySummary: PropTypes.shape({
    has_data: PropTypes.bool,
    total_bids: PropTypes.number,
    optimal_count: PropTypes.number,
    acceptable_count: PropTypes.number,
    suboptimal_count: PropTypes.number,
    error_count: PropTypes.number,
    avg_score: PropTypes.number,
    optimal_rate: PropTypes.number,
    accuracy_rate: PropTypes.number,
    all_decisions: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.number,
      bid_number: PropTypes.number,
      position: PropTypes.string,
      user_bid: PropTypes.string,
      optimal_bid: PropTypes.string,
      score: PropTypes.number,
      correctness: PropTypes.string,
      impact: PropTypes.string,
      helpful_hint: PropTypes.string
    }))
  })
};

export default BiddingGovernorPanel;

// Export sub-components for testing
export {
  PrincipleBadge,
  GovernorExplanation,
  BidComparison,
  BiddingDecisionCard,
  BiddingSummaryHeader,
  mapToPhysicsPrinciple,
  BIDDING_PRINCIPLES
};
