/**
 * TournamentComparisonTable.jsx
 *
 * Physics Audit Component - Side-by-side comparison of tournament player decisions
 * versus the V3 Logic Stack recommendations.
 *
 * This is the "truth-testing" layer showing:
 * - Tournament Action vs. Engine Optimal Bid
 * - Survival Status (SAFE/SURVIVED/FAILED/LUCKY)
 * - Score Comparison (Actual vs. Theoretical)
 * - Reasoning Gap with educational feedback
 *
 * Used in the Hand Review Modal for ACBL imported hands.
 */

import React from 'react';
import PropTypes from 'prop-types';
import './TournamentComparisonTable.css';

/**
 * Survival status badge component
 */
const SurvivalBadge = ({ status, panicIndex }) => {
  const statusConfig = {
    SAFE: { className: 'survival-safe', label: 'SAFE', icon: null },
    SURVIVED: { className: 'survival-survived', label: 'SURVIVED', icon: null },
    FAILED: { className: 'survival-failed', label: 'FAILED', icon: null },
    LUCKY: { className: 'survival-lucky', label: 'LUCKY', icon: null }
  };

  const config = statusConfig[status] || statusConfig.SAFE;

  return (
    <span className={`survival-badge ${config.className}`}>
      {config.icon && <span className="survival-icon">{config.icon}</span>}
      {config.label}
      {panicIndex > 0 && (
        <span className="panic-indicator" title={`Panic Index: ${panicIndex}`}>
          ({panicIndex})
        </span>
      )}
    </span>
  );
};

SurvivalBadge.propTypes = {
  status: PropTypes.string.isRequired,
  panicIndex: PropTypes.number
};

/**
 * Score delta indicator
 */
const ScoreDelta = ({ actual, theoretical }) => {
  const delta = actual - theoretical;
  const isPositive = delta > 0;
  const isNeutral = delta === 0;

  return (
    <div className={`score-delta ${isPositive ? 'positive' : isNeutral ? 'neutral' : 'negative'}`}>
      <span className="delta-arrow">
        {isPositive ? '+' : isNeutral ? '=' : ''}
      </span>
      <span className="delta-value">{delta}</span>
    </div>
  );
};

ScoreDelta.propTypes = {
  actual: PropTypes.number.isRequired,
  theoretical: PropTypes.number.isRequired
};

/**
 * Audit category badge
 */
const AuditCategoryBadge = ({ category }) => {
  const categoryConfig = {
    lucky_overbid: { className: 'category-lucky', label: 'Lucky Overbid' },
    penalty_trap: { className: 'category-penalty', label: 'Penalty Trap' },
    signal_error: { className: 'category-signal', label: 'Signal Error' },
    logic_aligned: { className: 'category-aligned', label: 'Logic Aligned' },
    rule_violation: { className: 'category-violation', label: 'Rule Violation' }
  };

  const config = categoryConfig[category] || { className: '', label: category || 'Pending' };

  return (
    <span className={`audit-category-badge ${config.className}`}>
      {config.label}
    </span>
  );
};

AuditCategoryBadge.propTypes = {
  category: PropTypes.string
};

/**
 * Main Tournament Comparison Table Component
 */
const TournamentComparisonTable = ({
  acblData,
  engineData,
  showDDS = true,
  onViewDetails
}) => {
  // Handle missing data gracefully
  if (!acblData || !engineData) {
    return (
      <div className="audit-container audit-loading">
        <p>Loading audit data...</p>
      </div>
    );
  }

  const {
    tournament_bid,
    tournament_contract,
    tournament_score,
    tournament_tricks,
    panic_index = 0
  } = acblData;

  const {
    optimal_bid,
    theoretical_score,
    survival_status = 'SAFE',
    rescue_action,
    matched_rule,
    audit_category,
    educational_feedback,
    dds_par_score,
    dds_par_contract,
    quadrant
  } = engineData;

  // Determine if tournament player's action was correct
  const isAligned = tournament_bid === optimal_bid;

  return (
    <div className="audit-container">
      <h3 className="audit-header">
        Tournament vs. Logic Audit
        {quadrant && (
          <span className={`quadrant-badge quadrant-${quadrant.toLowerCase()}`}>
            {quadrant}
          </span>
        )}
      </h3>

      <table className="comparison-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Tournament Player</th>
            <th>Bidding Master V3</th>
          </tr>
        </thead>
        <tbody>
          {/* Action/Bid Comparison */}
          <tr>
            <td><strong>Action</strong></td>
            <td className={isAligned ? '' : 'mismatch-cell'}>
              {tournament_bid || tournament_contract || '-'}
            </td>
            <td className="optimal-cell">
              {optimal_bid || '-'}
              {matched_rule && (
                <span className="rule-tag" title={matched_rule}>
                  [{matched_rule.substring(0, 20)}...]
                </span>
              )}
            </td>
          </tr>

          {/* Contract (if different from bid) */}
          {tournament_contract && tournament_contract !== tournament_bid && (
            <tr>
              <td><strong>Final Contract</strong></td>
              <td>{tournament_contract}</td>
              <td className="optimal-cell">-</td>
            </tr>
          )}

          {/* Survival Status */}
          <tr>
            <td><strong>Survival Status</strong></td>
            <td>
              <SurvivalBadge
                status={survival_status}
                panicIndex={panic_index}
              />
            </td>
            <td>
              {rescue_action ? (
                <span className="rescue-action">
                  Rescue: <strong>{rescue_action}</strong>
                </span>
              ) : (
                <span className="no-rescue">No rescue needed</span>
              )}
            </td>
          </tr>

          {/* Result/Score */}
          <tr>
            <td><strong>Result</strong></td>
            <td>
              <span className="score-value">{tournament_score}</span>
              {tournament_tricks !== undefined && (
                <span className="tricks-info">({tournament_tricks} tricks)</span>
              )}
            </td>
            <td>
              <span className="score-value theoretical">{theoretical_score}</span>
              <ScoreDelta actual={tournament_score} theoretical={theoretical_score} />
            </td>
          </tr>

          {/* DDS Par (if available) */}
          {showDDS && dds_par_score !== undefined && (
            <tr>
              <td><strong>DDS Par</strong></td>
              <td colSpan="2" className="dds-row">
                <span className="dds-contract">{dds_par_contract || 'N/A'}</span>
                <span className="dds-score">Par: {dds_par_score}</span>
              </td>
            </tr>
          )}

          {/* Audit Category */}
          <tr>
            <td><strong>Classification</strong></td>
            <td colSpan="2">
              <AuditCategoryBadge category={audit_category} />
            </td>
          </tr>
        </tbody>
      </table>

      {/* Reasoning Gap / Educational Feedback */}
      {educational_feedback && (
        <div className="logic-delta">
          <h4>Reasoning Gap</h4>
          <p className="feedback-text">{educational_feedback}</p>
        </div>
      )}

      {/* Danger Meter (if panic index is high) */}
      {panic_index > 30 && (
        <div className="danger-meter-container">
          <div className="danger-meter">
            <div
              className="danger-fill"
              style={{ width: `${Math.min(panic_index, 100)}%` }}
            />
            <span className="danger-label">Panic Index: {panic_index}</span>
          </div>
        </div>
      )}

      {/* View Details Button */}
      {onViewDetails && (
        <div className="audit-actions">
          <button
            className="view-details-btn"
            onClick={onViewDetails}
          >
            View Full Analysis
          </button>
        </div>
      )}
    </div>
  );
};

TournamentComparisonTable.propTypes = {
  acblData: PropTypes.shape({
    tournament_bid: PropTypes.string,
    tournament_contract: PropTypes.string,
    tournament_score: PropTypes.number,
    tournament_tricks: PropTypes.number,
    panic_index: PropTypes.number
  }),
  engineData: PropTypes.shape({
    optimal_bid: PropTypes.string,
    theoretical_score: PropTypes.number,
    survival_status: PropTypes.string,
    rescue_action: PropTypes.string,
    matched_rule: PropTypes.string,
    audit_category: PropTypes.string,
    educational_feedback: PropTypes.string,
    dds_par_score: PropTypes.number,
    dds_par_contract: PropTypes.string,
    quadrant: PropTypes.string
  }),
  showDDS: PropTypes.bool,
  onViewDetails: PropTypes.func
};

export default TournamentComparisonTable;
