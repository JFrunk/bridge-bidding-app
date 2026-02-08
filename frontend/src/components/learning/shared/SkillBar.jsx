import React from 'react';
import { getPerformanceLevel } from '../types/flow-types';
import './SkillBar.css';

/**
 * SkillBar - Horizontal progress bar with color thresholds
 *
 * @param {Object} props
 * @param {string} props.name - Skill name
 * @param {number} props.percentage - Progress percentage (0-100)
 * @param {boolean} [props.showLabel=true] - Whether to show percentage label
 */
const SkillBar = ({ name, percentage, showLabel = true }) => {
  const level = getPerformanceLevel(percentage);

  return (
    <div className="skill-bar-row">
      <span className="skill-name">{name}</span>
      <div className="skill-track">
        <div
          className={`skill-fill ${level}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className={`skill-pct ${level}`}>{Math.round(percentage)}%</span>
      )}
    </div>
  );
};

export default SkillBar;
