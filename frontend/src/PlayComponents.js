/**
 * PlayComponents.js - UI components for card play phase
 *
 * Components:
 * - TurnIndicator: Shows whose turn it is with animation
 * - ContractDisplay: Shows the final contract
 * - PlayTable: Shows current trick and 4 positions
 * - PlayableCard: Clickable card for user play
 * - ScoreDisplay: Shows final score after 13 tricks
 */

import React from 'react';
import './PlayComponents.css';
import { TurnIndicator, CompactTurnIndicator } from './components/play/TurnIndicator';

/**
 * Get suit display order based on trump suit
 * Trump on left, then highest opposite color suit descending
 * No Trump: S, H, C, D
 */
export function getSuitOrder(trumpStrain) {
  // No trump case
  if (!trumpStrain || trumpStrain === 'NT') {
    return ['♠', '♥', '♣', '♦'];
  }

  const strainToSuit = {
    'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣',
    '♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣'
  };

  const trumpSuit = strainToSuit[trumpStrain] || trumpStrain;
  const isRed = trumpSuit === '♥' || trumpSuit === '♦';

  if (trumpSuit === '♥') {
    return ['♥', '♠', '♦', '♣']; // Red trump: Hearts, Spades, Diamonds, Clubs
  } else if (trumpSuit === '♦') {
    return ['♦', '♠', '♥', '♣']; // Red trump: Diamonds, Spades, Hearts, Clubs
  } else if (trumpSuit === '♠') {
    return ['♠', '♥', '♣', '♦']; // Black trump: Spades, Hearts, Clubs, Diamonds
  } else if (trumpSuit === '♣') {
    return ['♣', '♥', '♠', '♦']; // Black trump: Clubs, Hearts, Spades, Diamonds
  }

  // Default fallback
  return ['♠', '♥', '♣', '♦'];
}

/**
 * Display the bidding auction history as a compact reference
 */
export function BiddingSummary({ auction }) {
  if (!auction || auction.length === 0) return null;

  // Group auction into rows of 4 (North, East, South, West)
  const rows = [];
  for (let i = 0; i < auction.length; i += 4) {
    rows.push(auction.slice(i, i + 4));
  }

  return (
    <div className="bidding-summary">
      <h4>Bidding</h4>
      <div className="bidding-summary-table">
        <div className="bidding-summary-header">
          <span>N</span>
          <span>E</span>
          <span>S</span>
          <span>W</span>
        </div>
        {rows.map((row, rowIndex) => (
          <div key={rowIndex} className="bidding-summary-row">
            {[0, 1, 2, 3].map(col => (
              <span key={col} className="bidding-summary-cell">
                {row[col]?.bid || '-'}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Display the contract with level, strain, declarer, and doubled status
 */
export function ContractDisplay({ contract }) {
  if (!contract) return null;

  const { level, strain, declarer, doubled } = contract;
  const doubledText = doubled === 2 ? 'XX' : doubled === 1 ? 'X' : '';

  return (
    <div className="contract-display">
      <h3>Contract</h3>
      <div className="contract-details">
        <span className="contract-bid">
          {level}{strain}{doubledText}
        </span>
        <span className="contract-declarer">
          by {declarer}
        </span>
      </div>
    </div>
  );
}

/**
 * Display a card that can be clicked to play
 */
export function PlayableCard({ card, onClick, disabled }) {
  const suitColor = card.suit === '♥' || card.suit === '♦' ? 'suit-red' : 'suit-black';
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };
  const displayRank = rankMap[card.rank] || card.rank;

  return (
    <div
      className={`playable-card ${disabled ? 'disabled' : 'clickable'}`}
      onClick={() => !disabled && onClick(card)}
    >
      <div className={`card-corner top-left ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{card.suit}</span>
      </div>
      <div className={`card-center ${suitColor}`}>
        <span className="suit-symbol-large">{card.suit}</span>
      </div>
      <div className={`card-corner bottom-right ${suitColor}`}>
        <span className="rank">{displayRank}</span>
        <span className="suit-symbol-small">{card.suit}</span>
      </div>
    </div>
  );
}

/**
 * Display current trick in progress
 */
export function CurrentTrick({ trick, positions, trickWinner, trickComplete }) {
  console.log('🃏 CurrentTrick received:', { trick, trick_length: trick?.length, trickWinner, trickComplete });

  if (!trick || trick.length === 0) {
    return (
      <div className="current-trick empty">
        <p>Waiting for cards...</p>
      </div>
    );
  }

  // DEFENSIVE: Only show the first 4 cards (a complete trick)
  // This prevents display issues if backend has more than 4 cards
  const displayTrick = trick.slice(0, 4);
  if (trick.length > 4) {
    console.error('⚠️ WARNING: Trick has more than 4 cards!', {
      trick_length: trick.length,
      trick_data: trick
    });
  }

  const suitColor = (suit) => suit === '♥' || suit === '♦' ? 'suit-red' : 'suit-black';
  const rankMap = { 'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10' };

  // Position name mapping
  const positionNames = {
    'N': 'North',
    'E': 'East',
    'S': 'South',
    'W': 'West'
  };

  return (
    <div className="current-trick">
      {displayTrick.map(({ card, position }, index) => {
        const displayRank = rankMap[card.rank] || card.rank;
        const isWinner = trickComplete && position === trickWinner;
        return (
          <div key={index} className={`trick-card-wrapper ${isWinner ? 'winner' : ''}`}>
            <div className="trick-position-label">{position}</div>
            <div className="trick-card">
              <span className={`trick-rank ${suitColor(card.suit)}`}>
                {displayRank}
              </span>
              <span className={`trick-suit ${suitColor(card.suit)}`}>
                {card.suit}
              </span>
            </div>
            {isWinner && <div className="winner-badge">Winner!</div>}
          </div>
        );
      })}
      {trickComplete && trickWinner && (
        <div className="trick-winner-announcement">
          {positionNames[trickWinner]} wins the trick!
        </div>
      )}
    </div>
  );
}

/**
 * Main play table showing 4 positions and current trick
 */
export function PlayTable({
  playState,
  userHand,
  dummyHand,
  onCardPlay,
  isUserTurn,
  auction,
  declarerHand,
  onDeclarerCardPlay,
  isDeclarerTurn,
  onDummyCardPlay,
  isDummyTurn
}) {
  if (!playState) return null;

  const { contract, current_trick, tricks_won, next_to_play, dummy, trick_complete, trick_winner } = playState;

  // Determine which positions are user (South) and dummy
  const userPosition = 'S';
  const dummyPosition = dummy;
  const declarerPosition = contract.declarer;

  // User is dummy if South is dummy position
  const userIsDummy = dummyPosition === 'S';

  // User is declarer if South is declarer
  const userIsDeclarer = declarerPosition === 'S';

  // Position mapping for display (clockwise from North)
  const positions = ['N', 'E', 'S', 'W'];

  // Get suit order based on trump
  const suitOrder = getSuitOrder(contract.strain);

  // DEBUG: Log what should be displayed
  console.log('👁️ Hand Display Logic:', {
    dummyPosition,
    declarerPosition,
    userIsDeclarer,
    userIsDummy,
    'North should show': dummyPosition === 'N',
    'East should show': dummyPosition === 'E',
    'South should show': true,
    'West should show': dummyPosition === 'W',
    'dummyHand exists': !!dummyHand,
    'dummyHand card count': dummyHand?.length || 0
  });

  // DEBUG: Log actual rendering decisions
  console.log('🎴 Actual Rendering:', {
    'North WILL render': dummyPosition === 'N' && !!dummyHand,
    'East WILL render': dummyPosition === 'E' && !!dummyHand,
    'West WILL render': dummyPosition === 'W' && !!dummyHand,
    'South WILL render': true
  });

  // Calculate tricks for consolidated header
  const tricksNeeded = contract.level + 6;
  const declarerSide = (declarerPosition === 'N' || declarerPosition === 'S') ? 'NS' : 'EW';
  const tricksWonBySide = declarerSide === 'NS'
    ? (tricks_won.N || 0) + (tricks_won.S || 0)
    : (tricks_won.E || 0) + (tricks_won.W || 0);
  const totalTricksPlayed = Object.values(tricks_won).reduce((sum, tricks) => sum + tricks, 0);
  const tricksRemaining = 13 - totalTricksPlayed;
  const tricksLost = 13 - tricksWonBySide - tricksRemaining;

  return (
    <div className="play-table">
      {/* Consolidated Contract Header - All contract info in one horizontal row */}
      <div className="contract-header-consolidated">
        {/* Unified Tricks Bar - Won (green left) | Remaining (dark center) | Lost (red right) */}
        <div className="unified-tricks-bar">
          <div className="tricks-won-section" style={{width: `${(tricksWonBySide / 13) * 100}%`}}>
            {tricksWonBySide > 0 && <span className="tricks-count">{tricksWonBySide}</span>}
          </div>
          <div className="tricks-remaining-section" style={{width: `${(tricksRemaining / 13) * 100}%`}}>
            {tricksRemaining > 0 && <span className="tricks-count">{tricksRemaining}</span>}
          </div>
          <div className="tricks-lost-section" style={{width: `${(tricksLost / 13) * 100}%`}}>
            {tricksLost > 0 && <span className="tricks-count">{tricksLost}</span>}
          </div>
        </div>

        {/* Contract Display - Large font */}
        <div className="contract-display-large">
          <div className="contract-text">
            {contract.level}{contract.strain === 'N' ? 'NT' : contract.strain}
          </div>
          <div className="declarer-text">by {declarerPosition}</div>
        </div>

        {/* Tricks Summary - Vertical stack */}
        <div className="tricks-summary">
          <div className="trick-stat">
            <span className="stat-label">Won:</span>
            <span className="stat-value">{tricksWonBySide}</span>
          </div>
          <div className="trick-stat">
            <span className="stat-label">Lost:</span>
            <span className="stat-value">{tricksLost}</span>
          </div>
          <div className="trick-stat">
            <span className="stat-label">Remaining:</span>
            <span className="stat-value">{tricksRemaining}</span>
          </div>
        </div>

        {/* Bidding Summary - Full height, scrollable */}
        <div className="bidding-summary-compact">
          <div className="bidding-header">Bidding</div>
          <div className="bidding-auction-scroll">
            {auction && auction.map((bidObject, index) => {
              const playerIndex = index % 4;
              const playerLabel = ['N', 'E', 'S', 'W'][playerIndex];
              return (
                <div key={index} className="bid-row">
                  <span className="bid-player">{playerLabel}</span>
                  <span className="bid-value">{bidObject.bid}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="play-area">
        {/* North position */}
        <div className="position position-north">
          <div className="position-label">
            North
            <CompactTurnIndicator position="N" isActive={next_to_play === 'N'} />
            {dummyPosition === 'N' && ' (Dummy)'}
            {declarerPosition === 'N' && userIsDummy && ' (You control as dummy)'}
          </div>
          {/* Show North's hand if it's dummy */}
          {dummyPosition === 'N' && dummyHand && (
            <div className="dummy-hand">
              {suitOrder.map(suit => (
                <div key={suit} className="suit-group">
                  {dummyHand.filter(card => card.suit === suit).map((card, index) => (
                    <PlayableCard
                      key={`${suit}-${index}`}
                      card={card}
                      onClick={userIsDeclarer ? onDummyCardPlay : () => {}}
                      disabled={userIsDeclarer ? !isDummyTurn : true}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}
          {declarerPosition === 'N' && userIsDummy && declarerHand && (
            <div className="declarer-hand">
              {suitOrder.map(suit => (
                <div key={suit} className="suit-group">
                  {declarerHand.filter(card => card.suit === suit).map((card, index) => (
                    <PlayableCard
                      key={`${suit}-${index}`}
                      card={card}
                      onClick={onDeclarerCardPlay}
                      disabled={!isDeclarerTurn}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Current trick in center */}
        <CurrentTrick
          trick={current_trick}
          positions={positions}
          trickWinner={trick_winner}
          trickComplete={trick_complete}
        />

        {/* East and West positions container */}
        <div className="east-west-container">
        <div className="position position-east">
          <div className="position-label">
            East
            <CompactTurnIndicator position="E" isActive={next_to_play === 'E'} />
            {dummyPosition === 'E' && ' (Dummy)'}
          </div>
          {/* Show East's hand if it's dummy */}
          {dummyPosition === 'E' && dummyHand && (
            <div className="dummy-hand">
              {suitOrder.map(suit => (
                <div key={suit} className="suit-group">
                  {dummyHand.filter(card => card.suit === suit).map((card, index) => (
                    <PlayableCard
                      key={`${suit}-${index}`}
                      card={card}
                      onClick={userIsDeclarer ? onDummyCardPlay : () => {}}
                      disabled={userIsDeclarer ? !isDummyTurn : true}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="position position-west">
          <div className="position-label">
            West
            <CompactTurnIndicator position="W" isActive={next_to_play === 'W'} />
            {dummyPosition === 'W' && ' (Dummy)'}
          </div>
          {/* Show West's hand if it's dummy */}
          {dummyPosition === 'W' && dummyHand && (
            <div className="dummy-hand">
              {suitOrder.map(suit => (
                <div key={suit} className="suit-group">
                  {dummyHand.filter(card => card.suit === suit).map((card, index) => (
                    <PlayableCard
                      key={`${suit}-${index}`}
                      card={card}
                      onClick={userIsDeclarer ? onDummyCardPlay : () => {}}
                      disabled={userIsDeclarer ? !isDummyTurn : true}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
        </div>

        {/* South position (user) */}
        <div className="position position-south">
          <div className="position-label">
            South (You)
            <CompactTurnIndicator position="S" isActive={next_to_play === 'S' && !userIsDummy} />
            {userIsDummy && ' - Dummy'}
          </div>
          {userHand && userHand.length > 0 && (
            <div className="user-play-hand">
              {suitOrder.map(suit => (
                <div key={suit} className="suit-group">
                  {userHand.filter(card => card.suit === suit).map((card, index) => (
                    <PlayableCard
                      key={`${suit}-${index}`}
                      card={card}
                      onClick={onCardPlay}
                      disabled={!isUserTurn}
                    />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Display final score after 13 tricks
 */
export function ScoreDisplay({ scoreData, onClose }) {
  if (!scoreData) return null;

  const { contract, tricks_taken, result, score, made } = scoreData;

  return (
    <div className="score-modal-overlay" onClick={onClose}>
      <div className="score-modal" onClick={e => e.stopPropagation()}>
        <h2>Hand Complete!</h2>

        <div className="score-details">
          <div className="score-row">
            <span>Contract:</span>
            <span className="score-value">
              {contract.level}{contract.strain}
              {contract.doubled === 2 ? 'XX' : contract.doubled === 1 ? 'X' : ''}
              {' by '}{contract.declarer}
            </span>
          </div>

          <div className="score-row">
            <span>Tricks Taken:</span>
            <span className="score-value">{tricks_taken}</span>
          </div>

          <div className="score-row">
            <span>Result:</span>
            <span className={`score-value ${made ? 'made' : 'down'}`}>
              {result}
            </span>
          </div>

          <div className="score-row total">
            <span>Score:</span>
            <span className={`score-value ${score >= 0 ? 'positive' : 'negative'}`}>
              {score >= 0 ? '+' : ''}{score}
            </span>
          </div>
        </div>

        <button className="close-button" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}

// Export TurnIndicator components for use in other files
export { TurnIndicator, CompactTurnIndicator };
