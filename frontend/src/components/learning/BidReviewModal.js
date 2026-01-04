/**
 * BidReviewModal Component - Bidding analysis with bid-by-bid breakdown
 *
 * Shows:
 * 1. User's hand with HCP, shape, and key features
 * 2. Full auction table (4 columns: N/E/S/W)
 * 3. Clickable user bids that expand to show analysis
 * 4. Communication context (what partner communicated, what you're communicating)
 *
 * Mirrors the play-by-play analysis pattern from HandReviewModal.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { getBiddingHandDetail } from '../../services/analyticsService';
import './BidReviewModal.css';

// Rating colors and labels
const RATING_CONFIG = {
  optimal: { color: '#059669', bgColor: '#ecfdf5', icon: '✓', label: 'Optimal' },
  acceptable: { color: '#3b82f6', bgColor: '#eff6ff', icon: '○', label: 'Acceptable' },
  suboptimal: { color: '#f59e0b', bgColor: '#fffbeb', icon: '!', label: 'Suboptimal' },
  error: { color: '#dc2626', bgColor: '#fef2f2', icon: '✗', label: 'Error' }
};

// Suit display helpers
const SUIT_SYMBOLS = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣', '♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣' };
const SUIT_COLORS = { '♠': '#1e40af', '♥': '#dc2626', '♦': '#ea580c', '♣': '#16a34a' };

const normalizeSuit = (suit) => SUIT_SYMBOLS[suit] || suit;

// Sort cards by rank within a suit
const sortCards = (cards) => {
  const rankOrder = ['A', 'K', 'Q', 'J', 'T', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
  return [...cards].sort((a, b) => {
    const aRank = a.rank || a.r;
    const bRank = b.rank || b.r;
    return rankOrder.indexOf(aRank) - rankOrder.indexOf(bRank);
  });
};

// Hand display component showing cards grouped by suit
const HandDisplay = ({ cards, hcp, shape, features, distributionPoints }) => {
  const cardsBySuit = useMemo(() => {
    const grouped = { '♠': [], '♥': [], '♦': [], '♣': [] };
    cards.forEach(card => {
      const suit = normalizeSuit(card.suit || card.s);
      if (grouped[suit]) {
        grouped[suit].push({ rank: card.rank || card.r, suit });
      }
    });
    Object.keys(grouped).forEach(suit => {
      grouped[suit] = sortCards(grouped[suit]);
    });
    return grouped;
  }, [cards]);

  const suitOrder = ['♠', '♥', '♦', '♣'];

  return (
    <div className="hand-display">
      <div className="hand-stats">
        <span className="stat hcp">{hcp} HCP</span>
        <span className="stat shape">{shape}</span>
        {distributionPoints > 0 && (
          <span className="stat dist">+{distributionPoints} dist</span>
        )}
      </div>
      {features && features.length > 0 && (
        <div className="hand-features">
          {features.map((f, i) => (
            <span key={i} className="feature-tag">{f}</span>
          ))}
        </div>
      )}
      <div className="hand-cards">
        {suitOrder.map(suit => (
          <div key={suit} className="suit-row">
            <span className="suit-symbol" style={{ color: SUIT_COLORS[suit] }}>{suit}</span>
            <span className="suit-cards">
              {cardsBySuit[suit].length > 0
                ? cardsBySuit[suit].map(c => c.rank).join(' ')
                : '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Auction table showing all bids with user bids clickable
const AuctionTable = ({ auctionHistory, dealer, userPosition, decisions, selectedBidIndex, onSelectBid }) => {
  const positions = ['N', 'E', 'S', 'W'];
  const dealerIndex = positions.indexOf(dealer || 'N');

  // Create decision lookup by bid position in auction
  const decisionByBidNumber = useMemo(() => {
    const map = {};
    decisions.forEach(d => {
      map[d.bid_number] = d;
    });
    return map;
  }, [decisions]);

  // Build auction rows (4 bids per row)
  const rows = useMemo(() => {
    if (!auctionHistory || auctionHistory.length === 0) return [];

    const result = [];
    let currentRow = new Array(4).fill(null);

    // Add empty cells before dealer
    for (let i = 0; i < dealerIndex; i++) {
      currentRow[i] = { empty: true };
    }

    let bidIndex = 0;
    let colIndex = dealerIndex;

    auctionHistory.forEach((bidInfo) => {
      const bid = typeof bidInfo === 'string' ? bidInfo : bidInfo.bid;
      const position = positions[colIndex];
      const bidNumber = bidIndex + 1;
      const decision = decisionByBidNumber[bidNumber];
      const isUserBid = position === userPosition && decision;

      currentRow[colIndex] = {
        bid,
        position,
        bidNumber,
        isUserBid,
        decision
      };

      colIndex++;
      bidIndex++;

      if (colIndex >= 4) {
        result.push([...currentRow]);
        currentRow = new Array(4).fill(null);
        colIndex = 0;
      }
    });

    // Add final incomplete row if needed
    if (currentRow.some(c => c !== null)) {
      result.push(currentRow);
    }

    return result;
  }, [auctionHistory, dealerIndex, decisionByBidNumber, userPosition]);

  const getBidClass = (cell) => {
    if (!cell || cell.empty) return '';
    let classes = ['auction-bid'];
    if (cell.isUserBid) {
      classes.push('user-bid');
      if (cell.decision?.correctness) {
        classes.push(`correctness-${cell.decision.correctness}`);
      }
    }
    if (cell.bidNumber === selectedBidIndex) {
      classes.push('selected');
    }
    return classes.join(' ');
  };

  return (
    <div className="auction-table">
      <div className="auction-header">
        {positions.map(pos => (
          <div key={pos} className={`auction-col-header ${pos === userPosition ? 'user-position' : ''}`}>
            {pos}
          </div>
        ))}
      </div>
      <div className="auction-body">
        {rows.map((row, rowIdx) => (
          <div key={rowIdx} className="auction-row">
            {row.map((cell, colIdx) => (
              <div
                key={colIdx}
                className={getBidClass(cell)}
                onClick={() => cell?.isUserBid && onSelectBid(cell.bidNumber)}
              >
                {cell?.empty ? '' : cell?.bid || ''}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

// Bid analysis panel showing feedback for selected bid
const BidAnalysisPanel = ({ decision }) => {
  if (!decision) {
    return (
      <div className="bid-analysis-panel empty">
        <p className="hint">Click on any of your bids (highlighted) to see analysis</p>
      </div>
    );
  }

  const rating = RATING_CONFIG[decision.correctness] || RATING_CONFIG.suboptimal;
  const isCorrect = decision.user_bid === decision.optimal_bid;

  return (
    <div className="bid-analysis-panel" style={{ borderLeftColor: rating.color }}>
      <div className="analysis-header">
        <div className="bid-comparison">
          <span className="your-bid">Your bid: <strong>{decision.user_bid}</strong></span>
          {!isCorrect && (
            <span className="optimal-bid">Optimal: <strong>{decision.optimal_bid}</strong></span>
          )}
        </div>
        <div className="rating-badge" style={{ backgroundColor: rating.bgColor, color: rating.color }}>
          <span className="rating-icon">{rating.icon}</span>
          <span className="rating-label">{rating.label}</span>
          <span className="rating-score">{decision.score}/10</span>
        </div>
      </div>

      {decision.partner_communicated && (
        <div className="communication-section partner">
          <div className="comm-label">What Partner Communicated:</div>
          <div className="comm-content">{decision.partner_communicated}</div>
        </div>
      )}

      {decision.you_communicated && (
        <div className="communication-section you">
          <div className="comm-label">What You're Communicating:</div>
          <div className="comm-content">{decision.you_communicated}</div>
        </div>
      )}

      {decision.reasoning && (
        <div className="reasoning-section">
          <div className="reasoning-label">Analysis:</div>
          <div className="reasoning-content">{decision.reasoning}</div>
        </div>
      )}

      {decision.helpful_hint && (
        <div className="hint-section">
          <div className="hint-label">Tip:</div>
          <div className="hint-content">{decision.helpful_hint}</div>
        </div>
      )}

      {decision.key_concept && (
        <div className="concept-tag">
          Key Concept: {decision.key_concept}
        </div>
      )}
    </div>
  );
};

// Main modal component
const BidReviewModal = ({ handId, onClose }) => {
  const [handData, setHandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBidIndex, setSelectedBidIndex] = useState(null);

  // Fetch bidding hand details
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await getBiddingHandDetail(handId);
        setHandData(data);
        // Auto-select first user bid if available
        if (data.bidding_decisions?.length > 0) {
          setSelectedBidIndex(data.bidding_decisions[0].bid_number);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (handId) {
      fetchData();
    }
  }, [handId]);

  // Get selected decision
  const selectedDecision = useMemo(() => {
    if (!selectedBidIndex || !handData?.bidding_decisions) return null;
    return handData.bidding_decisions.find(d => d.bid_number === selectedBidIndex);
  }, [selectedBidIndex, handData?.bidding_decisions]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        if (!handData?.bidding_decisions?.length) return;
        const decisions = handData.bidding_decisions;
        const currentIdx = decisions.findIndex(d => d.bid_number === selectedBidIndex);
        if (e.key === 'ArrowLeft' && currentIdx > 0) {
          setSelectedBidIndex(decisions[currentIdx - 1].bid_number);
        } else if (e.key === 'ArrowRight' && currentIdx < decisions.length - 1) {
          setSelectedBidIndex(decisions[currentIdx + 1].bid_number);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, handData?.bidding_decisions, selectedBidIndex]);

  if (loading) {
    return (
      <div className="bid-review-modal-overlay" onClick={onClose}>
        <div className="bid-review-modal" onClick={e => e.stopPropagation()}>
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading bidding analysis...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bid-review-modal-overlay" onClick={onClose}>
        <div className="bid-review-modal" onClick={e => e.stopPropagation()}>
          <div className="error-state">
            <p>Error: {error}</p>
            <button onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  if (!handData) {
    return null;
  }

  const { user_hand, auction_history, bidding_decisions, dealer, contract, user_position } = handData;

  return (
    <div className="bid-review-modal-overlay" onClick={onClose}>
      <div className="bid-review-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Bidding Review</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-content">
          {/* Contract result */}
          {contract && (
            <div className="contract-result">
              Final Contract: <strong>{contract}</strong>
            </div>
          )}

          {/* User's hand display */}
          {user_hand && (
            <div className="section hand-section">
              <div className="section-title">Your Hand ({user_position})</div>
              <HandDisplay
                cards={user_hand.cards || []}
                hcp={user_hand.hcp}
                shape={user_hand.shape}
                features={user_hand.features}
                distributionPoints={user_hand.distribution_points}
              />
            </div>
          )}

          {/* Auction table */}
          <div className="section auction-section">
            <div className="section-title">Auction</div>
            <AuctionTable
              auctionHistory={auction_history}
              dealer={dealer}
              userPosition={user_position}
              decisions={bidding_decisions || []}
              selectedBidIndex={selectedBidIndex}
              onSelectBid={setSelectedBidIndex}
            />
          </div>

          {/* Bid analysis */}
          <div className="section analysis-section">
            <div className="section-title">
              Bid Analysis
              {bidding_decisions?.length > 0 && (
                <span className="nav-hint">← → to navigate</span>
              )}
            </div>
            <BidAnalysisPanel decision={selectedDecision} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default BidReviewModal;
