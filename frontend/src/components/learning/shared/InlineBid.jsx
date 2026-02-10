import React from 'react';
import PropTypes from 'prop-types';
import { BidChip } from '../../shared/BidChip';
import './InlineBid.css';

/**
 * InlineBid - Inline bid badge for referencing bids within text
 *
 * Now uses BidChip internally for consistent suit coloring (Clubhouse theme).
 * Wraps BidChip with inline-specific styling for text flow.
 *
 * @param {Object} props
 * @param {string} props.bid - Bid string like "1H", "3NT", "Pass"
 */
const InlineBid = ({ bid }) => {
  if (!bid) return null;

  return (
    <span className="inline-bid-wrapper">
      <BidChip bid={bid} />
    </span>
  );
};

InlineBid.propTypes = {
  bid: PropTypes.string.isRequired,
};

export default InlineBid;
