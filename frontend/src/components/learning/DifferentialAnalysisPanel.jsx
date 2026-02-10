/**
 * DifferentialAnalysisPanel Component
 *
 * Displays a visual comparison between the user's bid and the optimal bid,
 * showing rule matching, feature gaps, and educational learning points.
 *
 * This is the core UI for the "Differential Analyzer" feedback system.
 */

import React, { useState, useEffect } from 'react';
import { BidChip } from '../shared/BidChip';
import './DifferentialAnalysisPanel.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Status icons for factor display
const STATUS_ICONS = {
  FAIL: '❌',
  WARNING: '⚠️',
  INFO: 'ℹ️',
  PASS: '✓'
};

// Rating colors
const RATING_COLORS = {
  optimal: '#22c55e',     // green
  acceptable: '#3b82f6',  // blue
  suboptimal: '#f59e0b',  // yellow/orange
  error: '#ef4444'        // red
};

/**
 * Factor display row
 */
const FactorRow = ({ factor }) => {
  const icon = STATUS_ICONS[factor.status] || '•';
  const isError = factor.status === 'FAIL';
  const isWarning = factor.status === 'WARNING';

  return (
    <div className={`factor-row ${isError ? 'error' : ''} ${isWarning ? 'warning' : ''}`}>
      <span className="factor-icon">{icon}</span>
      <div className="factor-content">
        <span className="factor-label">{factor.label}</span>
        <span className="factor-gap">{factor.gap}</span>
        {factor.impact && (
          <span className="factor-impact">{factor.impact}</span>
        )}
      </div>
      {factor.shortfall && (
        <span className="factor-shortfall">
          {factor.shortfall > 0 ? `+${factor.shortfall}` : factor.shortfall}
        </span>
      )}
    </div>
  );
};

/**
 * Rule card display
 */
const RuleCard = ({ rule, type }) => {
  const isOptimal = type === 'optimal';
  const matchRatio = `${rule.conditions_met}/${rule.conditions_total}`;
  const isFullMatch = rule.conditions_met === rule.conditions_total;

  return (
    <div className={`rule-card ${isOptimal ? 'optimal-rule' : 'user-rule'}`}>
      <div className="rule-header">
        <BidChip bid={rule.bid} />
        <span className="rule-priority">P{rule.priority}</span>
      </div>
      <div className="rule-body">
        <span className="rule-id">{rule.rule_id}</span>
        <span className="rule-description">{rule.description}</span>
      </div>
      <div className="rule-footer">
        <span className={`rule-match ${isFullMatch ? 'full' : 'partial'}`}>
          {matchRatio} conditions
        </span>
      </div>
    </div>
  );
};

/**
 * Physics summary display
 */
const PhysicsSummary = ({ physics }) => {
  if (!physics) return null;

  return (
    <div className="physics-summary">
      <div className="physics-grid">
        <div className="physics-item">
          <span className="physics-label">HCP</span>
          <span className="physics-value">{physics.hcp}</span>
        </div>
        <div className="physics-item">
          <span className="physics-label">Shape</span>
          <span className="physics-value">{physics.shape}</span>
        </div>
        {physics.lott_safe_level !== null && (
          <div className="physics-item">
            <span className="physics-label">LoTT Safe</span>
            <span className="physics-value">{physics.lott_safe_level}</span>
          </div>
        )}
        <div className="physics-item">
          <span className="physics-label">QT</span>
          <span className="physics-value">{physics.quick_tricks?.toFixed(1)}</span>
        </div>
        <div className="physics-item">
          <span className="physics-label">Working</span>
          <span className="physics-value">
            {(physics.working_hcp_ratio * 100).toFixed(0)}%
          </span>
        </div>
        {physics.is_balanced && (
          <div className="physics-item tag">
            <span className="physics-tag">Balanced</span>
          </div>
        )}
        {physics.is_misfit && (
          <div className="physics-item tag warning">
            <span className="physics-tag">Misfit</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Learning point display
 */
const LearningPoint = ({ learning, tutorialLink }) => {
  if (!learning) return null;

  const domainLabels = {
    safety: '🛡️ Safety',
    value: '💰 Value',
    control: '🎯 Control',
    tactical: '⚔️ Tactical',
    defensive: '🏰 Defensive',
    general: '📚 General'
  };

  return (
    <div className="learning-point">
      <div className="learning-header">
        <span className="learning-domain">
          {domainLabels[learning.domain] || domainLabels.general}
        </span>
      </div>
      <div className="learning-content">
        <p className="learning-reason">{learning.primary_reason}</p>
        <p className="learning-hint">{learning.learning_point}</p>
      </div>
      {tutorialLink && (
        <a href={tutorialLink} className="learning-link">
          Learn more →
        </a>
      )}
    </div>
  );
};

/**
 * Main DifferentialAnalysisPanel component
 */
const DifferentialAnalysisPanel = ({
  userBid,
  handCards,
  auctionHistory = [],
  position = 'S',
  vulnerability = 'None',
  dealer = 'N',
  // Optional: pre-loaded data (from evaluate-bid response)
  preloadedData = null,
  // Display options
  showPhysics = true,
  showRules = true,
  compact = false,
  onClose
}) => {
  const [data, setData] = useState(preloadedData);
  const [loading, setLoading] = useState(!preloadedData);
  const [error, setError] = useState(null);

  // Fetch differential analysis if not preloaded
  useEffect(() => {
    if (preloadedData) {
      setData(preloadedData);
      setLoading(false);
      return;
    }

    if (!userBid || !handCards || handCards.length === 0) {
      return;
    }

    const fetchAnalysis = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/api/differential-analysis`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_bid: userBid,
            hand_cards: handCards,
            auction_history: auctionHistory,
            position,
            vulnerability,
            dealer
          })
        });

        if (!response.ok) {
          throw new Error('Failed to load differential analysis');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [userBid, handCards, auctionHistory, position, vulnerability, dealer, preloadedData]);

  // Loading state
  if (loading) {
    return (
      <div className={`differential-panel ${compact ? 'compact' : ''}`}>
        <div className="differential-loading">
          <span className="loading-spinner">⏳</span>
          Analyzing differential...
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`differential-panel ${compact ? 'compact' : ''}`}>
        <div className="differential-error">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      </div>
    );
  }

  // No data state
  if (!data) {
    return null;
  }

  const isOptimal = data.rating === 'optimal';
  const ratingColor = RATING_COLORS[data.rating] || RATING_COLORS.suboptimal;

  return (
    <div className={`differential-panel ${compact ? 'compact' : ''}`} data-testid="differential-panel">
      {/* Header with close button */}
      <div className="differential-header">
        <h3 className="differential-title" data-testid="differential-title">Differential Analysis</h3>
        {onClose && (
          <button className="differential-close" onClick={onClose}>×</button>
        )}
      </div>

      {/* Bid comparison */}
      <div className="bid-comparison">
        <div className="bid-box user-bid">
          <span className="bid-label">Your Bid</span>
          <BidChip bid={data.user_bid} />
        </div>
        <div className="bid-arrow">→</div>
        <div className="bid-box optimal-bid">
          <span className="bid-label">Optimal</span>
          <BidChip bid={data.optimal_bid} />
        </div>
      </div>

      {/* Rating badge */}
      <div className="rating-badge" style={{ backgroundColor: ratingColor }} data-testid="differential-rating">
        <span className="rating-text" data-testid="rating-text">{data.rating}</span>
        <span className="rating-score" data-testid="rating-score">Score: {data.score}</span>
      </div>

      {/* Differential factors */}
      {data.differential?.factors?.length > 0 && (
        <div className="factors-section">
          <h4 className="section-title">Key Differences</h4>
          <div className="factors-list">
            {data.differential.factors.map((factor, idx) => (
              <FactorRow key={idx} factor={factor} />
            ))}
          </div>
        </div>
      )}

      {/* Rule comparison */}
      {showRules && !compact && (
        <div className="rules-comparison">
          {data.differential?.user_bid_rules?.length > 0 && (
            <div className="rules-column">
              <h4 className="column-title">Your Bid Matches</h4>
              {data.differential.user_bid_rules.map((rule, idx) => (
                <RuleCard key={idx} rule={rule} type="user" />
              ))}
            </div>
          )}
          {data.differential?.optimal_bid_rules?.length > 0 && (
            <div className="rules-column">
              <h4 className="column-title">Optimal Bid Matches</h4>
              {data.differential.optimal_bid_rules.map((rule, idx) => (
                <RuleCard key={idx} rule={rule} type="optimal" />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Physics summary */}
      {showPhysics && !compact && data.physics && (
        <PhysicsSummary physics={data.physics} />
      )}

      {/* Learning point */}
      {data.learning && (
        <div data-testid="learning-point-container">
          <LearningPoint
            learning={data.learning}
            tutorialLink={data.learning.tutorial_link}
          />
        </div>
      )}

      {/* Commentary (if not optimal) */}
      {!isOptimal && data.commentary_html && (
        <div
          className="differential-commentary"
          dangerouslySetInnerHTML={{ __html: data.commentary_html }}
        />
      )}
    </div>
  );
};

export default DifferentialAnalysisPanel;
