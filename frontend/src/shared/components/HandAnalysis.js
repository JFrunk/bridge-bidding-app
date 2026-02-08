/**
 * HandAnalysis Component
 *
 * Displays hand analysis including HCP, distribution points, and suit breakdown.
 * Used by both bidding and play modules.
 *
 * Props:
 *   - points: Object containing hand analysis
 *       {
 *         hcp: number,
 *         dist_points: number,
 *         total_points: number,
 *         suit_hcp: { '♠': number, '♥': number, '♦': number, '♣': number },
 *         suit_lengths: { '♠': number, '♥': number, '♦': number, '♣': number }
 *       }
 *   - vulnerability: String indicating vulnerability ('None', 'NS', 'EW', 'Both')
 *   - compact: Whether to show compact view (default: false)
 *   - strip: Whether to show as single-line strip (default: false) - for BID screen redesign
 */
import React from 'react';
import './HandAnalysis.css';

function HandAnalysis({ points, vulnerability, compact = false, strip = false }) {
  if (!points) return null;

  // Strip mode: Single horizontal line for BID screen redesign
  // Format: "12 total pts | ♠ 0(1) ♥ 0(3) ♦ 3(6) ♣ 7(3) | HCP: 10 + Dist: 2"
  if (strip) {
    return (
      <div className="hand-analysis-strip">
        <span className="strip-total">
          <strong>{points.total_points}</strong> total pts
        </span>
        <span className="strip-divider">|</span>
        <span className="strip-suits">
          <span className="suit-black">♠</span> {points.suit_hcp['♠']}({points.suit_lengths['♠']})
          {' '}
          <span className="suit-red">♥</span> {points.suit_hcp['♥']}({points.suit_lengths['♥']})
          {' '}
          <span className="suit-red">♦</span> {points.suit_hcp['♦']}({points.suit_lengths['♦']})
          {' '}
          <span className="suit-black">♣</span> {points.suit_hcp['♣']}({points.suit_lengths['♣']})
        </span>
        <span className="strip-divider">|</span>
        <span className="strip-breakdown">
          HCP: {points.hcp} + Dist: {points.dist_points}
        </span>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="hand-analysis hand-analysis-compact">
        <div className="hcp-display">
          <strong>{points.hcp}</strong> HCP
          {points.dist_points > 0 && <span> +{points.dist_points}</span>}
        </div>
      </div>
    );
  }

  return (
    <div className="hand-analysis">
      <h4>Hand Analysis {vulnerability && `(Vuln: ${vulnerability})`}</h4>
      <p>
        <strong>HCP:</strong> {points.hcp}
        {' + '}
        <strong>Dist:</strong> {points.dist_points}
        {' = '}
        <strong>Total: {points.total_points}</strong>
      </p>
      <div className="suit-points">
        <div>
          <span className="suit-black">♠</span> {points.suit_hcp['♠']} pts ({points.suit_lengths['♠']})
        </div>
        <div>
          <span className="suit-red">♥</span> {points.suit_hcp['♥']} pts ({points.suit_lengths['♥']})
        </div>
        <div>
          <span className="suit-red">♦</span> {points.suit_hcp['♦']} pts ({points.suit_lengths['♦']})
        </div>
        <div>
          <span className="suit-black">♣</span> {points.suit_hcp['♣']} pts ({points.suit_lengths['♣']})
        </div>
      </div>
    </div>
  );
}

export default HandAnalysis;
