/**
 * DecayChart - Step-chart visualization of NS trick accumulation
 *
 * Shows NS (user) cumulative tricks won, building up from 0.
 * Always from user's perspective regardless of who declared.
 *
 * Design:
 * - Step-chart (not smooth line) because tricks are discrete
 * - X-axis: 52 play positions (13 tricks x 4 cards)
 * - Y-axis: 0-13 tricks
 * - Bars from bottom: Cumulative NS tricks won (continuous, stay flat when EW wins)
 * - Dotted line: Best possible (optimal) tricks for NS
 * - Dashed line: Required tricks (to make or set)
 * - Blue line: Ascending potential (how many tricks NS should have won by now)
 *   Builds from 0 to dd_optimal. When an error occurs the line jumps up
 *   but bars don't, creating a visible gap = tricks lost.
 * - Red circles mark NS errors (where the gap widens)
 * - Hover/click synchronizes with HandReviewModal replay position
 */

import React, { useMemo, useCallback } from 'react';
import ChartHelp from '../help/ChartHelp';
import { nsSuccess } from '../../utils/seats';
import './DecayChart.css';

/**
 * DecayChart Component
 *
 * @param {Object} props
 * @param {Object} props.data - Decay curve data from API
 * @param {number[]} props.data.curve - Array of NS trick potentials (0-52 entries)
 * @param {Object[]} props.data.major_errors - Array of error objects with card_index
 * @param {Object[]} props.data.signal_warnings - Array of signal warning objects with card_index
 * @param {number[]} props.data.ns_tricks_cumulative - Cumulative NS tricks at each card
 * @param {number} props.data.dd_optimal_ns - Best possible tricks for NS (from double-dummy analysis)
 * @param {number} props.data.actual_tricks_ns - Actual tricks NS took
 * @param {boolean} props.data.ns_is_declarer - Whether NS was declaring side
 * @param {number} props.data.required_tricks - Tricks required to make/set
 * @param {number} props.replayPosition - Current position in HandReviewModal (0-52)
 * @param {function} props.onPositionChange - Callback when user clicks on chart
 * @param {number} props.width - SVG width (default 560)
 * @param {number} props.height - SVG height (default 180)
 * @param {Object} props.biddingContext - Optional bidding context for differential analysis
 * @param {string} props.biddingContext.domain - Diagnostic domain (safety, value, control, tactical, defensive)
 * @param {number} props.biddingContext.lott_safe_level - LoTT safe level if applicable
 * @param {number} props.biddingContext.bid_level - Actual bid level
 * @param {string} props.biddingContext.primary_reason - Primary reason for bidding issue
 * @param {Array} props.biddingContext.factors - Array of differential factors from bidding
 */
const DecayChart = ({
  data,
  replayPosition = 0,
  onPositionChange,
  width = 560,
  height = 180,
  biddingContext = null
}) => {
  // Extract data with defaults (before any conditional returns)
  const rawCurve = data?.curve || [];
  const major_errors = data?.major_errors || [];
  const signal_warnings = data?.signal_warnings || [];
  const ns_tricks_cumulative = data?.ns_tricks_cumulative || [];
  const dd_optimal_ns = data?.dd_optimal_ns ?? rawCurve[0] ?? 0;
  const actual_tricks_ns = data?.actual_tricks_ns ?? 0;
  const ns_is_declarer = data?.ns_is_declarer ?? true;
  const required_tricks = data?.required_tricks ?? 7;
  const hasData = rawCurve.length > 0 || ns_tricks_cumulative.length > 0;

  // Sanitize curve values and implement "persistence until falsification" logic
  // The potential line stays at its previous value until a play mathematically
  // seals that the previous potential is unreachable
  //
  // PHYSICS RULE: The Potential line can ONLY stay flat or drop.
  // It NEVER increases. Once potential is lost, it cannot be regained.
  const curve = useMemo(() => {
    if (rawCurve.length === 0) return [];

    // Starting potential is capped at dd_optimal_ns (best possible for NS)
    const initialPotential = Math.min(rawCurve[0] ?? dd_optimal_ns, dd_optimal_ns);

    // Build the curve with strict persistence - monotonically decreasing only
    const persistent = [];
    let currentPotential = initialPotential;

    for (let i = 0; i < rawCurve.length; i++) {
      const rawValue = rawCurve[i];

      // Calculate physical maximum possible at this point
      const tricksPlayed = Math.floor((i + 1) / 4);
      const tricksRemaining = 13 - tricksPlayed;
      const nsWonSoFar = ns_tricks_cumulative[i] ?? 0;
      const maxPossible = nsWonSoFar + tricksRemaining;

      // The new potential is capped at:
      // 1. The raw DDS value from backend
      // 2. The physical maximum possible
      // 3. The dd_optimal_ns (never show above optimal)
      // 4. CRITICALLY: The current potential (can never increase)
      const cappedValue = Math.min(rawValue, maxPossible, dd_optimal_ns, currentPotential);

      // Only update if this represents a true drop (falsification)
      // The line stays flat otherwise
      if (cappedValue < currentPotential) {
        currentPotential = cappedValue;
      }

      persistent.push(currentPotential);
    }

    return persistent;
  }, [rawCurve, ns_tricks_cumulative, dd_optimal_ns]);

  // Layout constants - right padding accommodates reference line labels
  const padding = useMemo(() => ({ top: 20, right: 75, bottom: 30, left: 35 }), []);
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Scaling functions (memoized for stability)
  const getX = useCallback((i) => padding.left + (i / 52) * chartWidth, [padding.left, chartWidth]);
  const getY = useCallback((val) => padding.top + chartHeight - (val / 13) * chartHeight, [padding.top, chartHeight]);

  // Ascending potential: "how many tricks should NS have won by now?"
  // Formula: dd_optimal - curve[i] + ns_tricks_cumulative[i]
  // - Starts at 0 (no tricks played yet)
  // - When NS wins a trick: goes up by 1 (same as bars → no gap change)
  // - When an error occurs: jumps up by 1 but bars don't → gap widens
  // - Ends at dd_optimal_ns (total optimal tricks)
  // The gap between this line and the bars = tricks lost to errors
  const ascendingPotential = useMemo(() => {
    if (curve.length === 0) return [];
    return curve.map((val, i) => {
      const cum = ns_tricks_cumulative[i] ?? 0;
      // Cap at dd_optimal_ns — when EW makes errors (gifts), cum can outpace
      // the curve drop, pushing the raw formula above optimal. The potential
      // line must never exceed the Best Possible line.
      return Math.min(dd_optimal_ns, dd_optimal_ns - val + cum);
    });
  }, [curve, ns_tricks_cumulative, dd_optimal_ns]);

  // Generate step path for the ascending potential line
  // Steps only at trick boundaries (every 4 cards), not mid-trick.
  // Uses the value at the END of each trick (last card of the 4).
  const pathData = useMemo(() => {
    if (ascendingPotential.length === 0) return '';

    // Start at 0 (before any tricks played)
    let d = `M ${getX(0)} ${getY(0)}`;

    for (let trick = 0; trick < 13; trick++) {
      const trickEnd = (trick + 1) * 4 - 1; // Last card index of this trick
      if (trickEnd >= ascendingPotential.length) break;

      const val = ascendingPotential[trickEnd];
      const trickStartX = getX(trick * 4);
      const trickEndX = getX((trick + 1) * 4);

      // At trick boundary: jump up to new value, then hold flat across trick
      d += ` H ${trickStartX} V ${getY(val)} H ${trickEndX}`;
    }

    // Extend to end if needed
    if (ascendingPotential.length < 52) {
      d += ` H ${getX(52)}`;
    }
    return d;
  }, [ascendingPotential, getX, getY]);

  // Generate bars for locked-in NS tricks - continuous bars for every trick
  // Bars stay flat when NS doesn't win (no drop to zero)
  const trickBars = useMemo(() => {
    if (ns_tricks_cumulative.length === 0) return [];

    const bars = [];
    let lastTrickCount = 0;

    // Add a bar for EVERY trick, maintaining cumulative level
    for (let trick = 0; trick < 13; trick++) {
      const cardIndex = (trick + 1) * 4 - 1; // Last card of trick
      if (cardIndex >= ns_tricks_cumulative.length) break;

      const nsTricksAtEnd = ns_tricks_cumulative[cardIndex];
      lastTrickCount = nsTricksAtEnd;

      // Always add a bar (even if 0 height, it keeps visual continuity)
      if (nsTricksAtEnd > 0) {
        bars.push({
          trickNumber: trick + 1,
          startX: getX(trick * 4),
          endX: getX((trick + 1) * 4),
          height: nsTricksAtEnd,
        });
      }
    }

    return bars;
  }, [ns_tricks_cumulative, getX]);

  // Error markers - filter to NS errors only
  const errorMarkers = useMemo(() => {
    return major_errors.filter(err =>
      err.error_type === 'ns_error' && err.card_index < ascendingPotential.length
    );
  }, [major_errors, ascendingPotential.length]);

  // Signal warning markers - plays where potential stayed flat but signal was suboptimal
  // These are educational warnings, not errors
  const signalMarkers = useMemo(() => {
    return signal_warnings.filter(warn =>
      warn.card_index !== undefined && warn.card_index < ascendingPotential.length
    );
  }, [signal_warnings, ascendingPotential.length]);

  // Note: We no longer display EW gift markers since the curve is capped at optimal.
  // The chart now focuses purely on user's errors (drops in potential) and signal warnings.

  // Handle click on chart
  const handleChartClick = useCallback((e) => {
    if (!onPositionChange) return;

    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const clickX = e.clientX - rect.left;

    const position = Math.round(((clickX - padding.left) / chartWidth) * 52);
    const clampedPosition = Math.max(0, Math.min(52, position));
    onPositionChange(clampedPosition);
  }, [onPositionChange, padding.left, chartWidth]);

  // Early return AFTER all hooks
  if (!hasData) {
    return (
      <div className="decay-chart-empty">
        <p>No decay curve data available</p>
      </div>
    );
  }

  // Grid lines at key trick values
  const gridLines = [0, 3, 6, 9, 13];

  // Trick markers along X-axis (every 4 cards = 1 trick)
  const trickMarkers = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52];

  // Current position indicator - tracks the ascending potential line
  const currentX = getX(replayPosition);
  const currentY = replayPosition > 0 && replayPosition <= ascendingPotential.length
    ? getY(ascendingPotential[replayPosition - 1])
    : getY(ascendingPotential[0] || 0);

  // Determine success/failure from NS perspective
  // Uses seats utility to handle both declaring and defending cases correctly
  const success = nsSuccess(ns_is_declarer, actual_tricks_ns, required_tricks);

  // Label for required line
  const requiredLabel = ns_is_declarer ? 'Need' : 'To Set';

  return (
    <div className="decay-chart-container">
      <div className="decay-chart-header">
        <div className="decay-chart-title-row">
          <span className="decay-chart-title">
            Your Trick Potential ({ns_is_declarer ? 'Declarer' : 'Defense'})
          </span>
          <ChartHelp chartType="trick-timeline" variant="icon" />
        </div>
        <span className="decay-chart-stats">
          Optimal: {dd_optimal_ns} | Actual: {actual_tricks_ns}
          <span className={success ? 'success-indicator' : 'failure-indicator'}>
            {success ? ' ✓' : ' ✗'}
          </span>
          {errorMarkers.length > 0 && (
            <span className="error-count"> | {errorMarkers.length} error{errorMarkers.length !== 1 ? 's' : ''}</span>
          )}
          {signalMarkers.length > 0 && (
            <span className="signal-warning-count" style={{ color: '#ed8936' }}>
              {' '}| {signalMarkers.length} signal{signalMarkers.length !== 1 ? 's' : ''}
            </span>
          )}
        </span>
      </div>

      <svg
        width={width}
        height={height}
        className="decay-chart"
        onClick={handleChartClick}
        style={{ cursor: onPositionChange ? 'crosshair' : 'default' }}
      >
        {/* Grid lines */}
        {gridLines.map(v => (
          <g key={v}>
            <line
              x1={padding.left}
              y1={getY(v)}
              x2={width - padding.right}
              y2={getY(v)}
              className="grid-line"
            />
            <text
              x={padding.left - 8}
              y={getY(v)}
              className="axis-label y-label"
            >
              {v}
            </text>
          </g>
        ))}

        {/* Trick boundary markers (vertical lines every 4 cards) */}
        {trickMarkers.slice(1, -1).filter((_, i) => i % 3 === 0).map(i => (
          <line
            key={i}
            x1={getX(i)}
            y1={padding.top}
            x2={getX(i)}
            y2={height - padding.bottom}
            className="trick-boundary"
          />
        ))}

        {/* Locked-in tricks bars (from bottom) with count labels just above bar tops */}
        {trickBars.map((bar, idx) => {
          const barTop = getY(bar.height);
          const barHeight = getY(0) - barTop;
          // Only show label when height changes from previous bar
          const prevHeight = idx > 0 ? trickBars[idx - 1].height : 0;
          const showLabel = bar.height > prevHeight;

          return (
            <g key={`bar-${idx}`}>
              <rect
                x={bar.startX}
                y={barTop}
                width={bar.endX - bar.startX - 1}
                height={barHeight}
                className="locked-tricks-bar"
              />
              {showLabel && (
                <text
                  x={(bar.startX + bar.endX) / 2}
                  y={barTop - 2}
                  className="bar-label"
                >
                  {bar.height}
                </text>
              )}
            </g>
          );
        })}

        {/* Optimal line (dotted horizontal) - best possible play */}
        <line
          x1={padding.left}
          y1={getY(dd_optimal_ns)}
          x2={width - padding.right}
          y2={getY(dd_optimal_ns)}
          className="dd-optimal-line"
        />
        <text
          x={width - padding.right + 3}
          y={getY(dd_optimal_ns)}
          className="axis-label reference-label dd-label"
        >
          Best - {dd_optimal_ns}
        </text>

        {/* Required tricks line (dashed) */}
        <line
          x1={padding.left}
          y1={getY(required_tricks)}
          x2={width - padding.right}
          y2={getY(required_tricks)}
          className="required-line"
        />
        <text
          x={width - padding.right + 3}
          y={getY(required_tricks)}
          className="axis-label reference-label required-label"
        >
          {requiredLabel} - {required_tricks}
        </text>

        {/* X-axis labels - show all 13 tricks */}
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map(trick => (
          <text
            key={`trick-${trick}`}
            x={getX((trick - 1) * 4 + 2)}
            y={height - 8}
            className="axis-label x-label"
          >
            {trick}
          </text>
        ))}

        {/* The decay curve line */}
        <path
          d={pathData}
          className="decay-line"
        />

        {/* Error markers (red circles - where user lost tricks) */}
        {errorMarkers.map((err, idx) => (
          <circle
            key={`err-${idx}`}
            cx={getX(err.card_index)}
            cy={getY(ascendingPotential[err.card_index] || 0)}
            r="5"
            className="error-marker"
          />
        ))}

        {/* Signal warning markers (yellow/orange diamonds - suboptimal signaling) */}
        {signalMarkers.map((warn, idx) => {
          const yPos = getY(ascendingPotential[warn.card_index] || 0);
          return (
            <g key={`signal-${idx}`} className="signal-warning-marker">
              <polygon
                points={`
                  ${getX(warn.card_index)},${yPos - 6}
                  ${getX(warn.card_index) + 5},${yPos}
                  ${getX(warn.card_index)},${yPos + 6}
                  ${getX(warn.card_index) - 5},${yPos}
                `}
                fill="#fffaf0"
                stroke="#ed8936"
                strokeWidth="2"
              />
            </g>
          );
        })}

        {/* Bidding context markers - LoTT ceiling line and domain indicators */}
        {biddingContext && biddingContext.lott_safe_level && biddingContext.bid_level > biddingContext.lott_safe_level && (
          <g className="bidding-context-group">
            {/* LoTT Ceiling line - shows where the safe level was */}
            <line
              x1={padding.left}
              y1={getY(biddingContext.lott_safe_level + 6)}
              x2={width - padding.right}
              y2={getY(biddingContext.lott_safe_level + 6)}
              className="lott-ceiling-line"
            />
            <text
              x={padding.left + 5}
              y={getY(biddingContext.lott_safe_level + 6) - 4}
              className="bidding-context-label lott-label"
            >
              LoTT Ceiling ({biddingContext.lott_safe_level + 6} tricks)
            </text>

            {/* Overbid indicator - triangle marker at required tricks showing overbid */}
            <g className="overbid-marker">
              <polygon
                points={`
                  ${width - padding.right - 10},${getY(required_tricks) - 8}
                  ${width - padding.right - 2},${getY(required_tricks)}
                  ${width - padding.right - 10},${getY(required_tricks) + 8}
                `}
                fill="rgba(239, 68, 68, 0.2)"
                stroke="#ef4444"
                strokeWidth="1.5"
              />
              <text
                x={width - padding.right - 25}
                y={getY(required_tricks) + 4}
                className="bidding-context-label overbid-label"
                textAnchor="end"
              >
                Overbid by {biddingContext.bid_level - biddingContext.lott_safe_level}
              </text>
            </g>
          </g>
        )}

        {/* Domain-specific bidding insight marker (shown at start of chart) */}
        {biddingContext && biddingContext.domain && biddingContext.primary_reason && (
          <g className="bidding-domain-marker">
            <rect
              x={padding.left + 10}
              y={padding.top + 5}
              width={Math.min(chartWidth - 20, 180)}
              height={22}
              rx="4"
              className={`domain-badge domain-${biddingContext.domain}`}
            />
            <text
              x={padding.left + 18}
              y={padding.top + 20}
              className="domain-text"
            >
              {biddingContext.domain === 'safety' && '⚠️ '}
              {biddingContext.domain === 'value' && '💰 '}
              {biddingContext.domain === 'control' && '🎯 '}
              {biddingContext.domain === 'tactical' && '♟️ '}
              {biddingContext.domain === 'defensive' && '🛡️ '}
              {biddingContext.primary_reason.length > 25
                ? biddingContext.primary_reason.substring(0, 25) + '...'
                : biddingContext.primary_reason}
            </text>
          </g>
        )}

        {/* Current position indicator */}
        {replayPosition > 0 && (
          <g className="position-indicator">
            <line
              x1={currentX}
              y1={padding.top}
              x2={currentX}
              y2={height - padding.bottom}
              className="position-line"
            />
            <circle
              cx={currentX}
              cy={currentY}
              r="6"
              className="position-dot"
            />
          </g>
        )}

        {/* Axis lines */}
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          className="axis-line"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          className="axis-line"
        />
      </svg>

      {/* Legend */}
      <div className="decay-chart-legend">
        <div className="legend-item">
          <span className="legend-swatch locked-bar-swatch"></span>
          <span>Tricks Won</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch decay-line-swatch"></span>
          <span>Potential</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch dd-line-swatch"></span>
          <span>Best Possible</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch required-line-swatch"></span>
          <span>{requiredLabel}</span>
        </div>
        {errorMarkers.length > 0 && (
          <div className="legend-item">
            <span className="legend-swatch error-swatch"></span>
            <span>Your Errors</span>
          </div>
        )}
        {biddingContext && biddingContext.lott_safe_level && (
          <div className="legend-item">
            <span className="legend-swatch lott-swatch"></span>
            <span>LoTT Ceiling</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default DecayChart;
