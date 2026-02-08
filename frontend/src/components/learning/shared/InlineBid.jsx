import React from 'react';
import PropTypes from 'prop-types';
import { formatBid } from '../types/flow-types';
import './InlineBid.css';

/**
 * InlineBid - Inline bid badge for referencing bids within text
 *
 * @param {Object} props
 * @param {string} props.bid - Bid string like "1H", "3NT", "Pass"
 */
const InlineBid = ({ bid }) => {
  const formattedBid = formatBid(bid);

  // Parse the formatted bid to identify and colorize suit symbols
  const renderBid = () => {
    if (!formattedBid) return null;

    // Handle special bids
    if (formattedBid === 'Pass' || formattedBid === 'X' || formattedBid === 'XX') {
      return <span>{formattedBid}</span>;
    }

    // Handle NT bids
    if (formattedBid.includes('NT')) {
      return <span>{formattedBid}</span>;
    }

    // Parse level and suit symbol
    const parts = [];
    for (let i = 0; i < formattedBid.length; i++) {
      const char = formattedBid[i];

      if (char === '♥' || char === '♦') {
        parts.push(
          <span key={i} className="suit-symbol red">{char}</span>
        );
      } else if (char === '♠' || char === '♣') {
        parts.push(
          <span key={i} className="suit-symbol black">{char}</span>
        );
      } else {
        parts.push(<span key={i}>{char}</span>);
      }
    }

    return <>{parts}</>;
  };

  return (
    <span className="inline-bid">
      {renderBid()}
    </span>
  );
};

InlineBid.propTypes = {
  bid: PropTypes.string.isRequired,
};

export default InlineBid;
