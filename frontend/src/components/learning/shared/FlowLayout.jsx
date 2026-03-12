/**
 * FlowLayout.jsx
 *
 * Three-zone container component for all learning flows.
 * Provides consistent header, felt zone, interaction zone, and optional action bar.
 *
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 */

import React, { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import './FlowLayout.css';

/**
 * FlowLayout - The core layout component for learning flows
 *
 * @param {string} title - Flow title shown in header
 * @param {string} stepIndicator - Optional step text like "Step 1 of 3"
 * @param {function} onClose - Optional close button handler
 * @param {ReactNode} feltContent - Content for the green felt zone
 * @param {ReactNode} interactionContent - Content for the cream interaction zone
 * @param {ReactNode} actionContent - Optional action bar content
 * @param {*} scrollKey - When this value changes, scroll zones reset to top
 */
function FlowLayout({
  title,
  stepIndicator = null,
  onClose = null,
  feltContent = null,
  interactionContent = null,
  actionContent = null,
  scrollKey = null
}) {
  const interactionRef = useRef(null);
  const feltRef = useRef(null);

  // Reset scroll position when scrollKey changes (e.g., flow state transitions)
  useEffect(() => {
    if (interactionRef.current) {
      interactionRef.current.scrollTop = 0;
    }
    if (feltRef.current) {
      feltRef.current.scrollTop = 0;
    }
  }, [scrollKey]);

  return (
    <div className="flow-container">
      {/* Header Zone */}
      <header className="flow-header">
        <div className="flow-header-left">
          <h1 className="flow-title">{title}</h1>
          {stepIndicator && (
            <span className="step-indicator">{stepIndicator}</span>
          )}
        </div>
        {onClose && (
          <button
            className="flow-close-button"
            onClick={onClose}
            aria-label="Close"
            type="button"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </header>

      {/* Felt Zone (Green) */}
      <div className="felt-zone" ref={feltRef}>
        <div className="felt-zone-content">
          {feltContent}
        </div>
      </div>

      {/* Interaction Zone (Cream) */}
      <div className="interaction-zone" ref={interactionRef}>
        {interactionContent}
      </div>

      {/* Action Bar (Optional) */}
      {actionContent && (
        <div className="action-bar">
          {actionContent}
        </div>
      )}
    </div>
  );
}

FlowLayout.propTypes = {
  title: PropTypes.string.isRequired,
  stepIndicator: PropTypes.string,
  onClose: PropTypes.func,
  feltContent: PropTypes.node,
  interactionContent: PropTypes.node,
  actionContent: PropTypes.node,
  scrollKey: PropTypes.any
};

export default FlowLayout;
