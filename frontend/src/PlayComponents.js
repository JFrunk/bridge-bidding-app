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
import { ContractHeader } from './components/play/ContractHeader';
import { CurrentTrickDisplay } from './components/play/CurrentTrickDisplay';
import { ScoreModal } from './components/play/ScoreModal';
import { PlayableCard as PlayableCardComponent } from './components/play/PlayableCard';
import { VerticalPlayableCard } from './components/play/VerticalPlayableCard';

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
 * MIGRATED: Now uses PlayableCard component from components/play/
 */
export function PlayableCard({ card, onClick, disabled }) {
  return <PlayableCardComponent card={card} onClick={() => onClick(card)} disabled={disabled} />;
}

/**
 * Display current trick in progress
 * MIGRATED: Now uses CurrentTrickDisplay component from components/play/
 */
export function CurrentTrick({ trick, positions, trickWinner, trickComplete }) {
  return <CurrentTrickDisplay trick={trick} trickWinner={trickWinner} trickComplete={trickComplete} />;
}

/**
 * CRITICAL: Determine if a hand should be visible based on bridge rules
 *
 * Bridge Visibility Rules:
 * 1. User (South) ALWAYS sees their own hand
 * 2. EVERYONE sees the dummy hand (after opening lead)
 * 3. Declarer's hand is ONLY visible if user IS the dummy (controls declarer)
 * 4. Defenders NEVER see each other's hands
 *
 * @param {string} position - The position to check ('N', 'E', 'S', 'W')
 * @param {string} dummyPosition - Which position is dummy
 * @param {string} declarerPosition - Which position is declarer
 * @param {boolean} userIsDummy - Is the user (South) the dummy?
 * @returns {boolean} - Should this hand be visible?
 */
function shouldShowHand(position, dummyPosition, declarerPosition, userIsDummy) {
  // Rule 1: Always show South (user's own hand)
  if (position === 'S') {
    return true;
  }

  // Rule 2: Always show dummy
  if (position === dummyPosition) {
    return true;
  }

  // Rule 3: Show declarer ONLY if user is dummy (user controls declarer)
  if (position === declarerPosition) {
    return userIsDummy;
  }

  // Rule 4: Never show other defenders
  return false;
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
  isDummyTurn,
  scoreData
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

  // CRITICAL: Centralized visibility rules - USE THESE for all hand rendering
  const showNorthHand = shouldShowHand('N', dummyPosition, declarerPosition, userIsDummy);
  const showEastHand = shouldShowHand('E', dummyPosition, declarerPosition, userIsDummy);
  const showSouthHand = shouldShowHand('S', dummyPosition, declarerPosition, userIsDummy);
  const showWestHand = shouldShowHand('W', dummyPosition, declarerPosition, userIsDummy);

  // DEBUG: Log visibility decisions
  console.log('👁️ Hand Visibility Rules Applied:', {
    dummyPosition,
    declarerPosition,
    userIsDummy,
    userIsDeclarer,
    visibility: {
      'North': showNorthHand,
      'East': showEastHand,
      'South': showSouthHand,
      'West': showWestHand
    },
    reason: {
      'North': showNorthHand ? (dummyPosition === 'N' ? 'DUMMY' : userIsDummy && declarerPosition === 'N' ? 'DECLARER (user controls)' : 'UNKNOWN') : 'HIDDEN',
      'East': showEastHand ? (dummyPosition === 'E' ? 'DUMMY' : userIsDummy && declarerPosition === 'E' ? 'DECLARER (user controls)' : 'UNKNOWN') : 'HIDDEN',
      'South': 'USER (always visible)',
      'West': showWestHand ? (dummyPosition === 'W' ? 'DUMMY' : userIsDummy && declarerPosition === 'W' ? 'DECLARER (user controls)' : 'UNKNOWN') : 'HIDDEN'
    }
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

  // Check if hand is complete
  const isHandComplete = totalTricksPlayed === 13;

  return (
    <div className="play-table">
      {/* Consolidated Contract Header - MIGRATED to ContractHeader component */}
      <ContractHeader contract={contract} tricksWon={tricks_won} auction={auction} scoreData={scoreData} />

      <div className="play-area">
        {/* North position */}
        <div className="position position-north">
          {/* CRITICAL: Use centralized visibility rule - prevents regression bugs */}
          {showNorthHand && !isHandComplete && (
            <div className={dummyPosition === 'N' ? "dummy-hand" : "declarer-hand"}>
              {suitOrder.map(suit => {
                const hand = dummyPosition === 'N' ? dummyHand : declarerHand;
                if (!hand || hand.length === 0) return null;
                return (
                  <div key={suit} className="suit-group">
                    {hand.filter(card => card.suit === suit).map((card, index) => (
                      <PlayableCard
                        key={`${suit}-${index}`}
                        card={card}
                        onClick={dummyPosition === 'N' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                        disabled={dummyPosition === 'N' ? (userIsDeclarer ? !isDummyTurn : true) : !isDeclarerTurn}
                      />
                    ))}
                  </div>
                );
              })}
            </div>
          )}
          <div className="position-label">
            North
            <CompactTurnIndicator position="N" isActive={next_to_play === 'N'} />
            {dummyPosition === 'N' && ' (Dummy)'}
            {declarerPosition === 'N' && userIsDummy && ' (Declarer - You control)'}
          </div>
        </div>

        {/* Current trick in center - CRITICAL: Positioned in center grid area */}
        <div className="current-trick-container">
          <CurrentTrick
            trick={current_trick}
            positions={positions}
            trickWinner={trick_winner}
            trickComplete={trick_complete}
          />
        </div>

        {/* West position - Left side (standard bridge layout) */}
        <div className="position position-west">
          <div className="position-label">
            West
            <CompactTurnIndicator position="W" isActive={next_to_play === 'W'} />
            {dummyPosition === 'W' && ' (Dummy)'}
            {declarerPosition === 'W' && userIsDummy && ' (Declarer - You control)'}
          </div>
          {/* CRITICAL: Use centralized visibility rule - prevents regression bugs */}
          {showWestHand && !isHandComplete && (
            <div className={dummyPosition === 'W' ? "dummy-hand" : "declarer-hand"}>
              {suitOrder.map(suit => {
                const hand = dummyPosition === 'W' ? dummyHand : declarerHand;
                if (!hand || hand.length === 0) return null;
                return (
                  <div key={suit} className="suit-group">
                    {hand.filter(card => card.suit === suit).map((card, index) => (
                      <VerticalPlayableCard
                        key={`${suit}-${index}`}
                        card={card}
                        onClick={dummyPosition === 'W' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                        disabled={dummyPosition === 'W' ? (userIsDeclarer ? !isDummyTurn : true) : !isDeclarerTurn}
                      />
                    ))}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* East position - Right side (standard bridge layout) */}
        <div className="position position-east">
          <div className="position-label">
            East
            <CompactTurnIndicator position="E" isActive={next_to_play === 'E'} />
            {dummyPosition === 'E' && ' (Dummy)'}
            {declarerPosition === 'E' && userIsDummy && ' (Declarer - You control)'}
          </div>
          {/* CRITICAL: Use centralized visibility rule - prevents regression bugs */}
          {showEastHand && !isHandComplete && (
            <div className={dummyPosition === 'E' ? "dummy-hand" : "declarer-hand"}>
              {suitOrder.map(suit => {
                const hand = dummyPosition === 'E' ? dummyHand : declarerHand;
                if (!hand || hand.length === 0) return null;
                return (
                  <div key={suit} className="suit-group">
                    {hand.filter(card => card.suit === suit).map((card, index) => (
                      <VerticalPlayableCard
                        key={`${suit}-${index}`}
                        card={card}
                        onClick={dummyPosition === 'E' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                        disabled={dummyPosition === 'E' ? (userIsDeclarer ? !isDummyTurn : true) : !isDeclarerTurn}
                      />
                    ))}
                  </div>
                );
              })}
            </div>
          )}
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
 * MIGRATED: Now uses ScoreModal component from components/play/
 */
export function ScoreDisplay({ scoreData, onClose, onDealNewHand, sessionData, onShowLearningDashboard, onPlayAnotherHand, onReplayHand }) {
  return <ScoreModal isOpen={!!scoreData} onClose={onClose} scoreData={scoreData} onDealNewHand={onDealNewHand} sessionData={sessionData} onShowLearningDashboard={onShowLearningDashboard} onPlayAnotherHand={onPlayAnotherHand} onReplayHand={onReplayHand} />;
}

// Export TurnIndicator components for use in other files
export { TurnIndicator, CompactTurnIndicator };
