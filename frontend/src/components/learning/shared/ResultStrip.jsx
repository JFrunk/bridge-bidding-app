import React from 'react';
import PropTypes from 'prop-types';
import './ResultStrip.css';

const DEFAULT_ICONS = {
  success: '\u2713',
  error: '\u2717',
  info: 'i'
};

/**
 * ResultStrip - Banner shown after every answer with success/error/info variants
 *
 * @param {string} type - Variant type: 'success' | 'error' | 'info'
 * @param {string} icon - Optional custom icon (emoji or character)
 * @param {string} message - Main message text
 * @param {string} detail - Optional secondary detail text
 */
function ResultStrip({ type = 'info', icon = null, message, detail = null }) {
  const displayIcon = icon || DEFAULT_ICONS[type] || DEFAULT_ICONS.info;

  return (
    <div
      className={`result-strip ${type}`}
      role="alert"
      aria-live="polite"
    >
      <span className="result-icon" aria-hidden="true">
        {displayIcon}
      </span>
      <span className="result-message">
        {message}
        {detail && (
          <span className="result-detail"> {detail}</span>
        )}
      </span>
    </div>
  );
}

ResultStrip.propTypes = {
  type: PropTypes.oneOf(['success', 'error', 'info']),
  icon: PropTypes.string,
  message: PropTypes.string.isRequired,
  detail: PropTypes.string
};

export default ResultStrip;
