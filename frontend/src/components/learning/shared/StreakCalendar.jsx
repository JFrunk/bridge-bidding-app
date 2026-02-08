import React from 'react';
import PropTypes from 'prop-types';
import './StreakCalendar.css';

/**
 * StreakCalendar - 7-day streak display showing practice history
 *
 * @param {Object} props
 * @param {Array<{label: string, status: 'done' | 'today' | 'future', count?: number}>} props.days
 */
const StreakCalendar = ({ days }) => {
  return (
    <div className="streak-bar">
      {days.map((day, index) => (
        <div key={index} className="streak-day">
          <div className={`streak-dot ${day.status}`}>
            {day.count !== undefined && day.count > 0 ? day.count : ''}
          </div>
          <span className="streak-label">{day.label}</span>
        </div>
      ))}
    </div>
  );
};

StreakCalendar.propTypes = {
  days: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      status: PropTypes.oneOf(['done', 'today', 'future']).isRequired,
      count: PropTypes.number,
    })
  ).isRequired,
};

export default StreakCalendar;
