/**
 * BiddingGapAnalysis Component
 *
 * Provides visual constraint debugging for bidding decisions.
 * Shows why specific bidding rules matched or didn't match,
 * with detailed gap information (e.g., "missing 1 HCP", "need diamond stopper").
 *
 * Features:
 * - Matched rules section: Shows rules that could apply to this hand
 * - Near-miss rules: Shows rules close to matching with specific gaps highlighted
 * - Constraint visualization: Color-coded pass/fail indicators for each condition
 * - Educational focus: Helps users understand the bidding logic
 */

import React, { useState, useEffect } from 'react';
import { BidChip } from '../shared/BidChip';
import './BiddingGapAnalysis.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Get suit color for display (used for non-bid suit indicators)
const getSuitColor = (suitStr) => {
  if (!suitStr) return '#1e293b';
  const s = suitStr.toLowerCase();
  if (s.includes('♥') || s.includes('heart') || s === 'h') return '#dc2626';
  if (s.includes('♦') || s.includes('diamond') || s === 'd') return '#dc2626';
  if (s.includes('♠') || s.includes('spade') || s === 's') return '#1e293b';
  if (s.includes('♣') || s.includes('club') || s === 'c') return '#1e293b';
  return '#1e293b';
};

// Condition type icons
const getConditionIcon = (type, passed) => {
  if (passed) return '✓';
  switch (type) {
    case 'comparison': return '📊';
    case 'numeric': return '#';
    case 'stopper': return '🛡️';
    case 'set': return '∈';
    case 'equality': return '=';
    case 'OR': return '∨';
    case 'NOT': return '¬';
    default: return '•';
  }
};

// Format condition key for display (snake_case to readable)
const formatConditionKey = (key) => {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
    .replace(/Hcp/g, 'HCP')
    .replace(/Nt/g, 'NT');
};

// Single condition display
const ConditionDisplay = ({ condition, compact = false }) => {
  const isPassed = condition.passed;
  const icon = getConditionIcon(condition.type, isPassed);

  // For compact mode, only show failed conditions
  if (compact && isPassed) return null;

  return (
    <div className={`gap-condition ${isPassed ? 'passed' : 'failed'}`}>
      <span className="condition-icon">{icon}</span>
      <span className="condition-key">{formatConditionKey(condition.key)}</span>
      <span className="condition-value">
        {isPassed ? (
          <span className="value-pass">✓ {formatValue(condition.actual)}</span>
        ) : (
          <>
            <span className="value-actual">{formatValue(condition.actual)}</span>
            <span className="value-arrow">→</span>
            <span className="value-required">{formatValue(condition.required)}</span>
          </>
        )}
      </span>
      {condition.gap && !isPassed && (
        <span className="condition-gap">{condition.gap}</span>
      )}
      {condition.min_shortfall && (
        <span className="condition-shortfall">need +{condition.min_shortfall}</span>
      )}
    </div>
  );
};

// Format values for display
const formatValue = (value) => {
  if (value === null || value === undefined) return 'none';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'object') {
    if (value.min !== undefined || value.max !== undefined) {
      const parts = [];
      if (value.min !== undefined) parts.push(`≥${value.min}`);
      if (value.max !== undefined) parts.push(`≤${value.max}`);
      return parts.join(', ');
    }
    return JSON.stringify(value);
  }
  return String(value);
};

// Rule card showing matched or near-miss rule
const RuleCard = ({ rule, isMatched, expanded, onToggle }) => {
  // Count passed/failed conditions
  const passedCount = rule.conditions?.filter(c => c.passed).length || 0;
  const failedCount = rule.conditions?.filter(c => !c.passed).length || 0;

  return (
    <div className={`gap-rule-card ${isMatched ? 'matched' : 'near-miss'}`}>
      <div className="rule-header" onClick={onToggle}>
        <BidChip bid={rule.bid} />
        <div className="rule-info">
          <div className="rule-description">{rule.description || rule.rule_id}</div>
          <div className="rule-meta">
            <span className="rule-category">{rule.category}</span>
            {!isMatched && (
              <span className="rule-gaps">
                {failedCount} gap{failedCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
        <div className="rule-status">
          {isMatched ? (
            <span className="status-matched">✓ Matched</span>
          ) : (
            <span className="status-gap-count">{passedCount}/{passedCount + failedCount}</span>
          )}
        </div>
        <span className={`expand-icon ${expanded ? 'expanded' : ''}`}>▼</span>
      </div>

      {expanded && (
        <div className="rule-details">
          {/* Show trigger if present */}
          {rule.trigger && (
            <div className={`trigger-info ${rule.trigger_matched ? 'passed' : 'failed'}`}>
              <span className="trigger-label">Auction Pattern:</span>
              <span className="trigger-pattern">{rule.trigger}</span>
              {!rule.trigger_matched && rule.trigger_gap && (
                <span className="trigger-gap">{rule.trigger_gap}</span>
              )}
            </div>
          )}

          {/* Show conditions */}
          <div className="conditions-list">
            {rule.conditions?.map((cond, idx) => (
              <ConditionDisplay key={idx} condition={cond} compact={isMatched} />
            ))}

            {/* For matched rules, show summary */}
            {isMatched && rule.conditions?.length > 0 && (
              <div className="conditions-summary">
                All {rule.conditions.length} conditions satisfied
              </div>
            )}
          </div>

          {/* Show forcing info */}
          {rule.forcing && rule.forcing !== 'none' && (
            <div className="forcing-info">
              <span className="forcing-label">Forcing:</span>
              <span className={`forcing-level ${rule.forcing}`}>
                {rule.forcing === 'one_round' ? '1 Round' :
                 rule.forcing === 'game' ? 'Game Force' : rule.forcing}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Hand features summary for context
const FeaturesSummary = ({ features }) => {
  if (!features) return null;

  return (
    <div className="gap-features-summary">
      <div className="features-grid">
        <div className="feature-item">
          <span className="feature-label">HCP</span>
          <span className="feature-value">{features.hcp ?? '—'}</span>
        </div>
        <div className="feature-item">
          <span className="feature-label">Shape</span>
          <span className="feature-value">{features.shape || '—'}</span>
        </div>
        <div className="feature-item">
          <span className="feature-label">Balanced</span>
          <span className="feature-value">{features.is_balanced ? 'Yes' : 'No'}</span>
        </div>
        {features.longest_suit && (
          <div className="feature-item">
            <span className="feature-label">Long Suit</span>
            <span className="feature-value" style={{ color: getSuitColor(features.longest_suit) }}>
              {features.longest_suit}
            </span>
          </div>
        )}
        {features.partner_last_bid && (
          <div className="feature-item">
            <span className="feature-label">Partner</span>
            <span className="feature-value">{features.partner_last_bid}</span>
          </div>
        )}
        {features.opening_bid && (
          <div className="feature-item">
            <span className="feature-label">Opening</span>
            <span className="feature-value">{features.opening_bid}</span>
          </div>
        )}
      </div>

      {/* Stopper summary */}
      <div className="stoppers-row">
        <span className="stoppers-label">Stoppers:</span>
        {['spades', 'hearts', 'diamonds', 'clubs'].map(suit => {
          const suitSymbol = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' }[suit];
          const hasStopper = features[`${suit}_stopped`];
          return (
            <span
              key={suit}
              className={`stopper-indicator ${hasStopper ? 'has-stopper' : 'no-stopper'}`}
              style={{ color: getSuitColor(suitSymbol) }}
              title={`${suit}: ${hasStopper ? 'stopped' : 'not stopped'}`}
            >
              {suitSymbol}
            </span>
          );
        })}
      </div>
    </div>
  );
};

// Main component
const BiddingGapAnalysis = ({
  handCards,
  auctionHistory = [],
  position = 'S',
  vulnerability = 'None',
  dealer = 'N',
  targetBid = null,  // Optional: filter to specific bid
  compact = false    // Compact mode for inline use
}) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedRules, setExpandedRules] = useState(new Set());
  const [showNearMisses, setShowNearMisses] = useState(true);

  // Fetch gap analysis
  useEffect(() => {
    if (!handCards || handCards.length === 0) return;

    const fetchAnalysis = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/api/bidding-gap-analysis`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            hand_cards: handCards,
            auction_history: auctionHistory,
            position,
            vulnerability,
            dealer,
            target_bid: targetBid
          })
        });

        if (!response.ok) {
          throw new Error('Failed to load gap analysis');
        }

        const data = await response.json();
        setAnalysis(data);

        // Auto-expand first matched rule and first near-miss
        const initialExpanded = new Set();
        if (data.matched_rules?.length > 0) {
          initialExpanded.add(data.matched_rules[0].rule_id);
        }
        if (data.near_misses?.length > 0) {
          initialExpanded.add(data.near_misses[0].rule_id);
        }
        setExpandedRules(initialExpanded);

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [handCards, auctionHistory, position, vulnerability, dealer, targetBid]);

  const toggleRule = (ruleId) => {
    setExpandedRules(prev => {
      const next = new Set(prev);
      if (next.has(ruleId)) {
        next.delete(ruleId);
      } else {
        next.add(ruleId);
      }
      return next;
    });
  };

  if (loading) {
    return (
      <div className={`bidding-gap-analysis ${compact ? 'compact' : ''}`}>
        <div className="gap-loading">
          <span className="loading-spinner">⏳</span>
          Analyzing bidding rules...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bidding-gap-analysis ${compact ? 'compact' : ''}`}>
        <div className="gap-error">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className={`bidding-gap-analysis ${compact ? 'compact' : ''}`}>
        <div className="gap-empty">
          <span className="empty-icon">📋</span>
          <p>Provide hand cards to see gap analysis</p>
        </div>
      </div>
    );
  }

  const { matched_rules = [], near_misses = [], hand_features, total_rules_checked } = analysis;

  return (
    <div className={`bidding-gap-analysis ${compact ? 'compact' : ''}`}>
      {/* Header */}
      <div className="gap-header">
        <h4 className="gap-title">Bidding Rule Analysis</h4>
        <span className="gap-count">
          {matched_rules.length} matched / {near_misses.length} near-miss
        </span>
      </div>

      {/* Features summary */}
      {!compact && <FeaturesSummary features={hand_features} />}

      {/* Matched rules section */}
      {matched_rules.length > 0 && (
        <div className="gap-section matched-section">
          <h5 className="section-title">
            <span className="section-icon">✓</span>
            Available Bids
          </h5>
          <div className="rules-list">
            {matched_rules.map(rule => (
              <RuleCard
                key={rule.rule_id}
                rule={rule}
                isMatched={true}
                expanded={expandedRules.has(rule.rule_id)}
                onToggle={() => toggleRule(rule.rule_id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Near-misses section */}
      {near_misses.length > 0 && (
        <div className="gap-section near-miss-section">
          <h5 className="section-title" onClick={() => setShowNearMisses(!showNearMisses)}>
            <span className="section-icon">⚡</span>
            Close But Not Quite
            <span className={`toggle-icon ${showNearMisses ? 'open' : ''}`}>▼</span>
          </h5>
          {showNearMisses && (
            <div className="rules-list">
              {near_misses.map(rule => (
                <RuleCard
                  key={rule.rule_id}
                  rule={rule}
                  isMatched={false}
                  expanded={expandedRules.has(rule.rule_id)}
                  onToggle={() => toggleRule(rule.rule_id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* No matches */}
      {matched_rules.length === 0 && near_misses.length === 0 && (
        <div className="gap-no-matches">
          <span className="no-matches-icon">🤔</span>
          <p>No matching or near-miss rules found.</p>
          <p className="no-matches-hint">
            Checked {total_rules_checked} rules. This hand may require V1 fallback or manual analysis.
          </p>
        </div>
      )}
    </div>
  );
};

export default BiddingGapAnalysis;
