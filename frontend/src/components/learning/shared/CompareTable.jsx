import React from 'react';
import PropTypes from 'prop-types';
import './CompareTable.css';

/**
 * CompareTable - Side-by-side comparison table component
 *
 * Used in lead quiz, debrief, and critical trick flows to show
 * player's choice vs optimal choice.
 *
 * @param {string} title - Optional table title/caption
 * @param {Array} columns - Column definitions with header and highlight flag
 * @param {Array} rows - Row data with label and cell values
 */
function CompareTable({ title = undefined, columns, rows }) {
  return (
    <table className="compare-table">
      {title && <caption>{title}</caption>}
      <thead>
        <tr>
          {/* Empty header for row label column */}
          <th></th>
          {columns.map((column, index) => (
            <th
              key={index}
              className={column.highlight ? 'highlight' : ''}
            >
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIndex) => (
          <tr key={rowIndex}>
            <td>{row.label}</td>
            {row.values.map((cell, cellIndex) => {
              const column = columns[cellIndex];
              const statusClass = cell.status || '';
              const highlightClass = column?.highlight ? 'highlight' : '';
              const classNames = [statusClass, highlightClass]
                .filter(Boolean)
                .join(' ');

              return (
                <td
                  key={cellIndex}
                  className={classNames || undefined}
                >
                  {cell.content}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

CompareTable.propTypes = {
  title: PropTypes.string,
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      header: PropTypes.string.isRequired,
      highlight: PropTypes.bool,
    })
  ).isRequired,
  rows: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      values: PropTypes.arrayOf(
        PropTypes.shape({
          content: PropTypes.node.isRequired,
          status: PropTypes.oneOf(['good', 'bad', 'neutral']),
        })
      ).isRequired,
    })
  ).isRequired,
};

export default CompareTable;
