import React from 'react';
import './ScoreRow.css';

/**
 * ScoreRow - Display a label/value pair with performance coloring
 *
 * @param {Object} props
 * @param {string} props.label - The label text
 * @param {string|number} props.value - The value to display
 * @param {'good'|'bad'|'neutral'} [props.status='neutral'] - Status for coloring
 */
const ScoreRow = ({ label, value, status = 'neutral' }) => {
  return (
    <div className="score-row">
      <span className="score-label">{label}</span>
      <span className={`score-value ${status}`}>{value}</span>
    </div>
  );
};

export default ScoreRow;
