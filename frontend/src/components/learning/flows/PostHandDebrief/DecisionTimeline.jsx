/**
 * DecisionTimeline.jsx
 *
 * Local component for Post-Hand Debrief.
 * Displays a vertical timeline of decisions with colored status dots.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { InlineBid } from '../../shared';
import './DecisionTimeline.css';

/**
 * Parse detail text to identify bids for inline display
 * @param {string} detail - Detail text that may contain bids
 * @param {string} playerBid - The player's bid if applicable
 * @param {string} optimalBid - The optimal bid if different
 * @returns {React.ReactNode[]}
 */
const renderDetailWithBids = (detail, playerBid, optimalBid) => {
  if (!detail) return null;

  // If no bids to highlight, return plain text
  if (!playerBid && !optimalBid) {
    return <span>{detail}</span>;
  }

  // For bid-type entries, render with InlineBid components
  if (playerBid) {
    if (optimalBid) {
      // Wrong bid - show both
      return (
        <>
          <span>Your bid: </span>
          <InlineBid bid={playerBid} />
          <span> — Better: </span>
          <InlineBid bid={optimalBid} />
        </>
      );
    } else {
      // Correct bid
      return (
        <>
          <span>Your bid: </span>
          <InlineBid bid={playerBid} />
        </>
      );
    }
  }

  return <span>{detail}</span>;
};

/**
 * Single timeline step
 */
const TimelineStep = ({ step }) => {
  const { label, detail, explanation, status, playerBid, optimalBid } = step;

  return (
    <div className={`timeline-step ${status}`}>
      <div className="timeline-dot-container">
        <div className="timeline-dot" aria-hidden="true" />
        <div className="timeline-line" aria-hidden="true" />
      </div>
      <div className="timeline-content">
        <div className="timeline-label">{label}</div>
        <div className="timeline-detail">
          {renderDetailWithBids(detail, playerBid, optimalBid)}
        </div>
        {explanation && (
          <div className="timeline-explanation">{explanation}</div>
        )}
      </div>
    </div>
  );
};

TimelineStep.propTypes = {
  step: PropTypes.shape({
    id: PropTypes.string.isRequired,
    round: PropTypes.number.isRequired,
    type: PropTypes.oneOf(['bid', 'play', 'result']).isRequired,
    label: PropTypes.string.isRequired,
    detail: PropTypes.string.isRequired,
    explanation: PropTypes.string,
    status: PropTypes.oneOf(['correct', 'wrong', 'neutral']).isRequired,
    playerBid: PropTypes.string,
    optimalBid: PropTypes.string
  }).isRequired
};

/**
 * DecisionTimeline - Vertical timeline of all decisions in the hand
 *
 * @param {Object} props
 * @param {TimelineStep[]} props.steps - Array of timeline steps
 */
const DecisionTimeline = ({ steps = [] }) => {
  if (!steps || steps.length === 0) {
    return (
      <div className="decision-timeline decision-timeline--empty">
        <p className="timeline-empty-message">No decisions to review</p>
      </div>
    );
  }

  return (
    <div className="decision-timeline" role="list" aria-label="Decision timeline">
      {steps.map((step, index) => (
        <TimelineStep
          key={step.id}
          step={step}
        />
      ))}
    </div>
  );
};

DecisionTimeline.propTypes = {
  steps: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      round: PropTypes.number.isRequired,
      type: PropTypes.oneOf(['bid', 'play', 'result']).isRequired,
      label: PropTypes.string.isRequired,
      detail: PropTypes.string.isRequired,
      explanation: PropTypes.string,
      status: PropTypes.oneOf(['correct', 'wrong', 'neutral']).isRequired,
      playerBid: PropTypes.string,
      optimalBid: PropTypes.string
    })
  )
};

export default DecisionTimeline;
