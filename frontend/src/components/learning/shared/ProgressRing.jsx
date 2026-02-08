import React from 'react';
import './ProgressRing.css';

/**
 * ProgressRing - Circular SVG progress indicator
 *
 * @param {Object} props
 * @param {number} props.percentage - Progress percentage (0-100)
 * @param {number} [props.size=64] - Size of the ring in pixels
 * @param {number} [props.strokeWidth=4] - Width of the ring stroke
 * @param {string} [props.label] - Optional center text (defaults to percentage)
 */
const ProgressRing = ({ percentage, size = 64, strokeWidth = 4, label }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percentage / 100);

  const displayLabel = label !== undefined ? label : `${Math.round(percentage)}%`;

  return (
    <div className="progress-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          className="ring-bg"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="ring-fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="ring-text">{displayLabel}</div>
    </div>
  );
};

export default ProgressRing;
