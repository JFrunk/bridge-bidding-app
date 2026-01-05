/**
 * DecayChart - Step-chart visualization of trick potential decay
 *
 * Shows declarer's maximum trick potential at each card played.
 * A flat line means optimal play; drops indicate mistakes.
 *
 * Design:
 * - Step-chart (not smooth line) because tricks are discrete
 * - X-axis: 52 play positions (13 tricks x 4 cards)
 * - Y-axis: 0-13 trick potential
 * - Red circles mark major errors
 * - Hover/click synchronizes with HandReviewModal replay position
 *
 * Physics:
 * - Horizontal steps: No decision made (waiting for next card)
 * - Downward steps: Mistake (potential lost)
 * - Upward steps: Defensive error (gift to declarer)
 * - Flat line: Perfect play
 */

import React, { useMemo, useCallback } from 'react';
import './DecayChart.css';

/**
 * DecayChart Component
 *
 * @param {Object} props
 * @param {Object} props.data - Decay curve data from API
 * @param {number[]} props.data.curve - Array of trick potentials (0-52 entries)
 * @param {Object[]} props.data.major_errors - Array of error objects with card_index
 * @param {number} props.replayPosition - Current position in HandReviewModal (0-52)
 * @param {function} props.onPositionChange - Callback when user clicks on chart
 * @param {number} props.width - SVG width (default 560)
 * @param {number} props.height - SVG height (default 160)
 */
const DecayChart = ({
  data,
  replayPosition = 0,
  onPositionChange,
  width = 560,
  height = 160
}) => {
  // Extract data with defaults (before any conditional returns)
  const curve = data?.curve || [];
  const major_errors = data?.major_errors || [];
  const hasData = curve.length > 0;

  // Layout constants
  const padding = useMemo(() => ({ top: 20, right: 20, bottom: 30, left: 35 }), []);
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Scaling functions (memoized for stability)
  const getX = useCallback((i) => padding.left + (i / 52) * chartWidth, [padding.left, chartWidth]);
  const getY = useCallback((val) => padding.top + chartHeight - (val / 13) * chartHeight, [padding.top, chartHeight]);

  // Generate step path
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

  // Error markers - filter to declarer errors only
  const errorMarkers = useMemo(() => {
    return major_errors.filter(err =>
      err.error_type === 'declarer_error' && err.card_index < curve.length
    );
  }, [major_errors, curve.length]);

  // Defensive gift markers (upward steps)
  const giftMarkers = useMemo(() => {
    return major_errors.filter(err =>
      err.error_type === 'defensive_gift' && err.card_index < curve.length
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

  return (
    <div className="decay-chart-container">
      <div className="decay-chart-header">
        <span className="decay-chart-title">Trick Potential</span>
        <span className="decay-chart-stats">
          Start: {curve[0] || 0} | End: {curve[curve.length - 1] || 0}
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

        {/* Defensive gift markers (green circles - upward steps) */}
        {giftMarkers.map((err, idx) => (
          <circle
            key={`gift-${idx}`}
            cx={getX(err.card_index)}
            cy={getY(curve[err.card_index] || 0)}
            r="5"
            className="gift-marker"
          />
        ))}

        {/* Error markers (red circles) */}
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
          <span className="legend-swatch decay-line-swatch"></span>
          <span>Trick Potential</span>
        </div>
        {errorMarkers.length > 0 && (
          <div className="legend-item">
            <span className="legend-swatch error-swatch"></span>
            <span>Errors</span>
          </div>
        )}
        {giftMarkers.length > 0 && (
          <div className="legend-item">
            <span className="legend-swatch gift-swatch"></span>
            <span>Defense Gifts</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default DecayChart;
