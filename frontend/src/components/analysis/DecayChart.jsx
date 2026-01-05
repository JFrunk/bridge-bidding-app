/**
 * DecayChart - Step-chart visualization of trick potential decay
 *
 * Shows NS (user) maximum trick potential at each card played.
 * Always from user's perspective regardless of who declared.
 *
 * Design:
 * - Step-chart (not smooth line) because tricks are discrete
 * - X-axis: 52 play positions (13 tricks x 4 cards)
 * - Y-axis: 0-13 trick potential
 * - Bars from bottom: Locked-in tricks won by NS
 * - Dotted line: DD optimal tricks for NS
 * - Dashed line: Required tricks (to make or set)
 * - Red circles mark NS errors
 * - Green circles mark EW gifts
 * - Hover/click synchronizes with HandReviewModal replay position
 *
 * Physics:
 * - Horizontal steps: No decision made (waiting for next card)
 * - Downward steps: NS mistake (potential lost)
 * - Upward steps: EW error (gift to NS)
 * - Flat line: Perfect play
 */

import React, { useMemo, useCallback } from 'react';
import ChartHelp from '../help/ChartHelp';
import './DecayChart.css';

/**
 * DecayChart Component
 *
 * @param {Object} props
 * @param {Object} props.data - Decay curve data from API
 * @param {number[]} props.data.curve - Array of NS trick potentials (0-52 entries)
 * @param {Object[]} props.data.major_errors - Array of error objects with card_index
 * @param {number[]} props.data.ns_tricks_cumulative - Cumulative NS tricks at each card
 * @param {number} props.data.dd_optimal_ns - DD optimal tricks for NS
 * @param {number} props.data.actual_tricks_ns - Actual tricks NS took
 * @param {boolean} props.data.ns_is_declarer - Whether NS was declaring side
 * @param {number} props.data.required_tricks - Tricks required to make/set
 * @param {number} props.replayPosition - Current position in HandReviewModal (0-52)
 * @param {function} props.onPositionChange - Callback when user clicks on chart
 * @param {number} props.width - SVG width (default 560)
 * @param {number} props.height - SVG height (default 180)
 */
const DecayChart = ({
  data,
  replayPosition = 0,
  onPositionChange,
  width = 560,
  height = 180
}) => {
  // Extract data with defaults (before any conditional returns)
  const curve = data?.curve || [];
  const major_errors = data?.major_errors || [];
  const ns_tricks_cumulative = data?.ns_tricks_cumulative || [];
  const dd_optimal_ns = data?.dd_optimal_ns ?? curve[0] ?? 0;
  const actual_tricks_ns = data?.actual_tricks_ns ?? 0;
  const ns_is_declarer = data?.ns_is_declarer ?? true;
  const required_tricks = data?.required_tricks ?? 7;
  const hasData = curve.length > 0;

  // Layout constants
  const padding = useMemo(() => ({ top: 20, right: 20, bottom: 30, left: 35 }), []);
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Scaling functions (memoized for stability)
  const getX = useCallback((i) => padding.left + (i / 52) * chartWidth, [padding.left, chartWidth]);
  const getY = useCallback((val) => padding.top + chartHeight - (val / 13) * chartHeight, [padding.top, chartHeight]);

  // Generate step path for the decay curve
  const pathData = useMemo(() => {
    if (curve.length === 0) return '';

    let d = `M ${getX(0)} ${getY(curve[0])}`;
    curve.forEach((val, i) => {
      if (i === 0) return;
      d += ` H ${getX(i)} V ${getY(val)}`;
    });
    if (curve.length < 52) {
      d += ` H ${getX(52)}`;
    }
    return d;
  }, [curve, getX, getY]);

  // Generate bars for locked-in NS tricks
  const trickBars = useMemo(() => {
    if (ns_tricks_cumulative.length === 0) return [];

    const bars = [];
    let lastTrickCount = 0;

    // Group by complete tricks (every 4 cards)
    for (let trick = 0; trick < 13; trick++) {
      const cardIndex = (trick + 1) * 4 - 1; // Last card of trick
      if (cardIndex >= ns_tricks_cumulative.length) break;

      const nsTricksAtEnd = ns_tricks_cumulative[cardIndex];
      if (nsTricksAtEnd > lastTrickCount) {
        // NS won this trick - add bar
        bars.push({
          trickNumber: trick + 1,
          startX: getX(trick * 4),
          endX: getX((trick + 1) * 4),
          height: nsTricksAtEnd,
        });
        lastTrickCount = nsTricksAtEnd;
      }
    }

    return bars;
  }, [ns_tricks_cumulative, getX]);

  // Error markers - filter to NS errors only
  const errorMarkers = useMemo(() => {
    return major_errors.filter(err =>
      err.error_type === 'ns_error' && err.card_index < curve.length
    );
  }, [major_errors, curve.length]);

  // EW gift markers (upward steps for NS)
  const giftMarkers = useMemo(() => {
    return major_errors.filter(err =>
      err.error_type === 'ew_gift' && err.card_index < curve.length
    );
  }, [major_errors, curve.length]);

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

  // Current position indicator
  const currentX = getX(replayPosition);
  const currentY = replayPosition > 0 && replayPosition <= curve.length
    ? getY(curve[replayPosition - 1])
    : getY(curve[0] || 0);

  // Determine success/failure
  const success = ns_is_declarer
    ? actual_tricks_ns >= required_tricks
    : actual_tricks_ns >= required_tricks;

  // Label for required line
  const requiredLabel = ns_is_declarer ? 'Need' : 'To Set';

  return (
    <div className="decay-chart-container">
      <div className="decay-chart-header">
        <div className="decay-chart-title-row">
          <span className="decay-chart-title">
            {ns_is_declarer ? 'Declarer View' : 'Defense View'}: NS Tricks
          </span>
          <ChartHelp chartType="trick-timeline" variant="icon" />
        </div>
        <span className="decay-chart-stats">
          DD: {dd_optimal_ns} | Actual: {actual_tricks_ns}
          <span className={success ? 'success-indicator' : 'failure-indicator'}>
            {success ? ' ✓' : ' ✗'}
          </span>
          {errorMarkers.length > 0 && (
            <span className="error-count"> | {errorMarkers.length} error{errorMarkers.length !== 1 ? 's' : ''}</span>
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

        {/* Locked-in tricks bars (from bottom) */}
        {trickBars.map((bar, idx) => (
          <rect
            key={`bar-${idx}`}
            x={bar.startX}
            y={getY(bar.height)}
            width={bar.endX - bar.startX - 1}
            height={getY(0) - getY(bar.height)}
            className="locked-tricks-bar"
          />
        ))}

        {/* DD Optimal line (dotted horizontal) */}
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
          DD
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
          {requiredLabel}
        </text>

        {/* X-axis labels */}
        <text
          x={padding.left}
          y={height - 8}
          className="axis-label x-label"
        >
          T1
        </text>
        <text
          x={getX(24)}
          y={height - 8}
          className="axis-label x-label"
        >
          T7
        </text>
        <text
          x={width - padding.right}
          y={height - 8}
          className="axis-label x-label"
        >
          T13
        </text>

        {/* The decay curve line */}
        <path
          d={pathData}
          className="decay-line"
        />

        {/* EW gift markers (green circles - upward steps) */}
        {giftMarkers.map((err, idx) => (
          <circle
            key={`gift-${idx}`}
            cx={getX(err.card_index)}
            cy={getY(curve[err.card_index] || 0)}
            r="5"
            className="gift-marker"
          />
        ))}

        {/* NS error markers (red circles) */}
        {errorMarkers.map((err, idx) => (
          <circle
            key={`err-${idx}`}
            cx={getX(err.card_index)}
            cy={getY(curve[err.card_index] || 0)}
            r="5"
            className="error-marker"
          />
        ))}

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
        {errorMarkers.length > 0 && (
          <div className="legend-item">
            <span className="legend-swatch error-swatch"></span>
            <span>NS Error</span>
          </div>
        )}
        {giftMarkers.length > 0 && (
          <div className="legend-item">
            <span className="legend-swatch gift-swatch"></span>
            <span>EW Gift</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default DecayChart;
