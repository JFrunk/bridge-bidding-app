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
 */
import React from 'react';
import './HandAnalysis.css';

function HandAnalysis({ points, vulnerability, compact = false }) {
  if (!points) return null;

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
