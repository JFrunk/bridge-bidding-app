import React, { useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import './RangeSlider.css';

/**
 * RangeSlider - Dual-endpoint range slider for HCP range estimation
 *
 * Uses two overlapping HTML range inputs for accessibility and native behavior.
 * The fill bar visually spans from lowValue to highValue.
 */
const RangeSlider = ({
  label = 'HCP Range',
  min = 0,
  max = 40,
  lowValue,
  highValue,
  onChange,
  disabled = false,
  showCorrect = false,
  correctLow,
  correctHigh,
}) => {
  const trackRef = useRef(null);

  // Calculate percentage positions for styling
  const lowPercent = ((lowValue - min) / (max - min)) * 100;
  const highPercent = ((highValue - min) / (max - min)) * 100;

  // Calculate correct range percentages if showing
  const correctLowPercent = showCorrect && correctLow !== undefined
    ? ((correctLow - min) / (max - min)) * 100
    : 0;
  const correctHighPercent = showCorrect && correctHigh !== undefined
    ? ((correctHigh - min) / (max - min)) * 100
    : 0;

  // Handle low value change - ensure it doesn't exceed high value
  const handleLowChange = useCallback((e) => {
    const newLow = parseInt(e.target.value, 10);
    if (newLow <= highValue) {
      onChange({ low: newLow, high: highValue });
    }
  }, [highValue, onChange]);

  // Handle high value change - ensure it doesn't go below low value
  const handleHighChange = useCallback((e) => {
    const newHigh = parseInt(e.target.value, 10);
    if (newHigh >= lowValue) {
      onChange({ low: lowValue, high: newHigh });
    }
  }, [lowValue, onChange]);

  // Format display value
  const displayValue = lowValue === highValue
    ? `${lowValue}`
    : `${lowValue}-${highValue}`;

  return (
    <div className={`range-slider ${disabled ? 'range-slider--disabled' : ''}`}>
      <label className="slider-label">{label}</label>

      <div className="slider-container">
        <div className="slider-track" ref={trackRef}>
          {/* Correct range overlay - shown when showCorrect is true */}
          {showCorrect && correctLow !== undefined && correctHigh !== undefined && (
            <div
              className="slider-correct"
              style={{
                left: `${correctLowPercent}%`,
                width: `${correctHighPercent - correctLowPercent}%`,
              }}
              aria-label={`Correct range: ${correctLow}-${correctHigh}`}
            />
          )}

          {/* Selected range fill */}
          <div
            className="slider-fill"
            style={{
              left: `${lowPercent}%`,
              width: `${highPercent - lowPercent}%`,
            }}
          />

          {/* Low value range input */}
          <input
            type="range"
            className="slider-input slider-input--low"
            min={min}
            max={max}
            value={lowValue}
            onChange={handleLowChange}
            disabled={disabled}
            aria-label={`${label} minimum value`}
            aria-valuemin={min}
            aria-valuemax={max}
            aria-valuenow={lowValue}
          />

          {/* High value range input */}
          <input
            type="range"
            className="slider-input slider-input--high"
            min={min}
            max={max}
            value={highValue}
            onChange={handleHighChange}
            disabled={disabled}
            aria-label={`${label} maximum value`}
            aria-valuemin={min}
            aria-valuemax={max}
            aria-valuenow={highValue}
          />
        </div>

        <span className="slider-value" aria-live="polite">
          {displayValue}
        </span>
      </div>
    </div>
  );
};

RangeSlider.propTypes = {
  label: PropTypes.string,
  min: PropTypes.number,
  max: PropTypes.number,
  lowValue: PropTypes.number.isRequired,
  highValue: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  showCorrect: PropTypes.bool,
  correctLow: PropTypes.number,
  correctHigh: PropTypes.number,
};

export default RangeSlider;
