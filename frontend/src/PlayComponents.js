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
import { CompactTurnIndicator } from './components/play/TurnIndicator';
import { ContractHeader } from './components/play/ContractHeader';
import { CurrentTrickDisplay } from './components/play/CurrentTrickDisplay';
import { LastTrickOverlay } from './components/play/LastTrickOverlay';
import { ScoreModal } from './components/play/ScoreModal';
import { PlayableCard as PlayableCardComponent } from './components/play/PlayableCard';
import Card from './shared/components/Card';
import { sortCards } from './shared/utils/cardUtils';

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
export function CurrentTrick({ trick, positions, trickWinner, trickComplete, nextToPlay }) {
  return <CurrentTrickDisplay trick={trick} trickWinner={trickWinner} trickComplete={trickComplete} nextToPlay={nextToPlay} />;
}

/**
 * CRITICAL: Determine if a hand should be visible based on bridge rules
 *
 * Bridge Visibility Rules:
 * 1. User (South) ALWAYS sees their own hand
 * 2. EVERYONE sees the dummy hand (ONLY after opening lead is made)
 * 3. Declarer's hand is ONLY visible if user IS the dummy (controls declarer)
 * 4. Defenders NEVER see each other's hands
 *
 * @param {string} position - The position to check ('N', 'E', 'S', 'W')
 * @param {string} dummyPosition - Which position is dummy
 * @param {string} declarerPosition - Which position is declarer
 * @param {boolean} userIsDummy - Is the user (South) the dummy?
 * @param {boolean} dummyRevealed - Has dummy been revealed? (after opening lead)
 * @returns {boolean} - Should this hand be visible?
 */
function shouldShowHand(position, dummyPosition, declarerPosition, userIsDummy, dummyRevealed, userPosition = 'S') {
  // Rule 1: Always show user's own hand
  if (position === userPosition) {
    return true;
  }

  // Rule 2: Show dummy ONLY after opening lead (when dummy_revealed is true)
  if (position === dummyPosition) {
    return dummyRevealed === true;
  }

  // Rule 3: Show declarer ONLY if user is dummy (user controls declarer)
  if (position === declarerPosition) {
    return userIsDummy;
  }

  // Rule 4: Never show other defenders
  return false;
}

/**
 * Map bridge positions to visual screen positions based on user's seat.
 * User always sits at the bottom. Positions rotate clockwise.
 *
 * @param {string} userPosition - User's bridge position ('S' or 'N')
 * @returns {Object} { bottom, top, left, right } -> bridge positions
 */
function getVisualPositions(userPosition) {
  // Standard rotation: user at bottom, partner at top, LHO left, RHO right
  const rotations = {
    'S': { bottom: 'S', top: 'N', left: 'W', right: 'E' },
    'N': { bottom: 'N', top: 'S', left: 'E', right: 'W' },
    'E': { bottom: 'E', top: 'W', left: 'N', right: 'S' },
    'W': { bottom: 'W', top: 'E', left: 'S', right: 'N' },
  };
  return rotations[userPosition] || rotations['S'];
}

const POSITION_NAMES = { 'N': 'North', 'E': 'East', 'S': 'South', 'W': 'West' };

/**
 * CRITICAL: Determine if a card is legal to play based on follow-suit rules
 *
 * Bridge Follow-Suit Rules:
 * 1. If first card in trick, any card is legal
 * 2. If trick has cards, must follow led suit if able
 * 3. If no cards in led suit, any card is legal (discard)
 *
 * @param {Object} card - Card to check {rank, suit}
 * @param {Array} hand - Player's current hand
 * @param {Array} currentTrick - Current trick cards [{card, player}, ...]
 * @returns {boolean} - Is this card legal to play?
 */
function isCardLegalToPlay(card, hand, currentTrick) {
  // Rule 1: First card in trick - any card is legal
  if (!currentTrick || currentTrick.length === 0) {
    return true;
  }

  // Rule 2: Determine led suit (first card in trick)
  const ledSuit = currentTrick[0].card.suit;

  // Rule 3: Check if player has any cards in led suit
  const hasLedSuit = hand.some(c => c.suit === ledSuit);

  // If player has led suit, they must play it
  if (hasLedSuit) {
    return card.suit === ledSuit;
  }

  // If player has no led suit, any card is legal
  return true;
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
  dealer,
  declarerHand,
  onDeclarerCardPlay,
  isDeclarerTurn,
  onDummyCardPlay,
  isDummyTurn,
  scoreData,
  // Last trick feature props
  showLastTrick,
  lastTrick,
  onShowLastTrick,
  onHideLastTrick,
  // Room mode: user's actual position (default South for solo play)
  userPosition: userPositionProp
}) {
  if (!playState) return null;

  const { contract, current_trick, tricks_won, next_to_play, dummy, trick_complete, trick_winner } = playState;

  // User position: use prop if provided, default to 'S' for solo play
  const userPosition = userPositionProp || 'S';
  const dummyPosition = dummy;
  const declarerPosition = contract.declarer;

  // User is dummy if user's position is dummy position
  const userIsDummy = dummyPosition === userPosition;

  // User is declarer if user's position is declarer
  const userIsDeclarer = declarerPosition === userPosition;

  // Visual position mapping: user always at bottom
  const vp = getVisualPositions(userPosition);

  // Position mapping for display (clockwise from North)
  const positions = ['N', 'E', 'S', 'W'];

  // Get suit order based on trump
  const suitOrder = getSuitOrder(contract.strain);

  // CRITICAL: Centralized visibility rules - USE THESE for all hand rendering
  // Pass dummy_revealed from playState to ensure dummy is only shown AFTER opening lead
  const dummyRevealed = playState.dummy_revealed || false;
  // Visibility by visual position (top/bottom/left/right)
  const showTopHand = shouldShowHand(vp.top, dummyPosition, declarerPosition, userIsDummy, dummyRevealed, userPosition);
  const showLeftHand = shouldShowHand(vp.left, dummyPosition, declarerPosition, userIsDummy, dummyRevealed, userPosition);
  const showRightHand = shouldShowHand(vp.right, dummyPosition, declarerPosition, userIsDummy, dummyRevealed, userPosition);
  const showBottomHand = shouldShowHand(vp.bottom, dummyPosition, declarerPosition, userIsDummy, dummyRevealed, userPosition);

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
      <ContractHeader contract={contract} tricksWon={tricks_won} auction={auction} dealer={dealer} scoreData={scoreData} />

      <div className="play-area">
        {/* Top position (partner's side) */}
        <div className="position position-north">
          {showTopHand && !isHandComplete ? (
            <div className={dummyPosition === vp.top ? "dummy-hand" : "declarer-hand"}>
              {suitOrder.map(suit => {
                const hand = dummyPosition === vp.top ? dummyHand : declarerHand;
                const handCards = hand?.cards || hand;
                if (!handCards || handCards.length === 0) return null;
                const suitCards = sortCards(handCards.filter(card => card.suit === suit));
                return (
                  <div key={suit} className="suit-group">
                    {suitCards.map((card, index) => {
                      const isMyTurn = dummyPosition === vp.top ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn;
                      const isLegalCard = isCardLegalToPlay(card, handCards, current_trick);
                      const isDisabled = !isMyTurn || !isLegalCard;
                      return (
                        <PlayableCard
                          key={`top-${card.rank}-${card.suit}`}
                          card={card}
                          onClick={dummyPosition === vp.top && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                          disabled={isDisabled}
                        />
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ) : !isHandComplete && (
            <Card isHidden customScaleClass="text-sm" />
          )}
          <div className="position-label">
            {POSITION_NAMES[vp.top]}
            <CompactTurnIndicator position={vp.top} isActive={next_to_play === vp.top} />
            {dummyPosition === vp.top && ' (Dummy)'}
            {declarerPosition === vp.top && userIsDummy && ' (Declarer - You control)'}
          </div>
        </div>

        {/* Current trick in center - CRITICAL: Positioned in center grid area */}
        <div className="current-trick-container">
          {showLastTrick && lastTrick ? (
            <LastTrickOverlay
              trick={lastTrick}
              trickNumber={playState.trick_history?.length || 0}
              onClose={onHideLastTrick}
            />
          ) : (
            <CurrentTrick
              trick={current_trick}
              positions={positions}
              trickWinner={trick_winner}
              trickComplete={trick_complete}
              nextToPlay={next_to_play}
            />
          )}
        </div>

        {/* Left position (user's LHO) */}
        <div className="position position-west">
          <div className="position-label">
            {POSITION_NAMES[vp.left]}
            <CompactTurnIndicator position={vp.left} isActive={next_to_play === vp.left} />
            {dummyPosition === vp.left && ' (Dummy)'}
            {declarerPosition === vp.left && userIsDummy && ' (Declarer - You control)'}
          </div>
          {showLeftHand && !isHandComplete ? (
            <div className="ew-hand-stack">
              {suitOrder.map(suit => {
                const hand = dummyPosition === vp.left ? dummyHand : declarerHand;
                const handCards = hand?.cards || hand;
                if (!handCards || handCards.length === 0) return null;
                const suitCards = sortCards(handCards.filter(card => card.suit === suit));
                if (suitCards.length === 0) return null;
                const isMyTurn = dummyPosition === vp.left ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn;
                return (
                  <div key={suit} className="ew-suit-row">
                    {suitCards.map((card, idx) => {
                      const isLegalCard = isCardLegalToPlay(card, handCards, current_trick);
                      const isDisabled = !isMyTurn || !isLegalCard;
                      const clickHandler = dummyPosition === vp.left && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay;
                      return (
                        <div key={`left-${card.rank}-${card.suit}`} className="ew-card-slot" style={{ zIndex: 10 + idx }}>
                          <Card
                            rank={card.rank}
                            suit={card.suit}
                            customScaleClass="text-sm"
                            selectable={!isDisabled}
                            onClick={() => clickHandler(card)}
                          />
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ) : !isHandComplete && (
            <div className="ew-hand-stack">
              <Card isHidden customScaleClass="text-sm" />
            </div>
          )}
        </div>

        {/* Right position (user's RHO) */}
        <div className="position position-east">
          <div className="position-label">
            {POSITION_NAMES[vp.right]}
            <CompactTurnIndicator position={vp.right} isActive={next_to_play === vp.right} />
            {dummyPosition === vp.right && ' (Dummy)'}
            {declarerPosition === vp.right && userIsDummy && ' (Declarer - You control)'}
          </div>
          {showRightHand && !isHandComplete ? (
            <div className="ew-hand-stack">
              {suitOrder.map(suit => {
                const hand = dummyPosition === vp.right ? dummyHand : declarerHand;
                const handCards = hand?.cards || hand;
                if (!handCards || handCards.length === 0) return null;
                const suitCards = sortCards(handCards.filter(card => card.suit === suit));
                if (suitCards.length === 0) return null;
                const isMyTurn = dummyPosition === vp.right ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn;
                return (
                  <div key={suit} className="ew-suit-row">
                    {suitCards.map((card, idx) => {
                      const isLegalCard = isCardLegalToPlay(card, handCards, current_trick);
                      const isDisabled = !isMyTurn || !isLegalCard;
                      const clickHandler = dummyPosition === vp.right && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay;
                      return (
                        <div key={`right-${card.rank}-${card.suit}`} className="ew-card-slot" style={{ zIndex: 10 + idx }}>
                          <Card
                            rank={card.rank}
                            suit={card.suit}
                            customScaleClass="text-sm"
                            selectable={!isDisabled}
                            onClick={() => clickHandler(card)}
                          />
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ) : !isHandComplete && (
            <div className="ew-hand-stack">
              <Card isHidden customScaleClass="text-sm" />
            </div>
          )}
        </div>

        {/* Bottom position (user) */}
        <div className="position position-south">
          <div className="position-label">
            {POSITION_NAMES[vp.bottom]} (You)
            <CompactTurnIndicator position={vp.bottom} isActive={next_to_play === vp.bottom && !userIsDummy} />
            {userIsDummy && ' - Dummy'}
          </div>
          {(() => {
            // When user is dummy, try dummyHand first, fallback to userHand
            const hand = (dummyPosition === userPosition ? (dummyHand || userHand) : userHand);
            const handCards = hand?.cards || hand;

            if (!handCards || handCards.length === 0) return null;

            return (
              <div className="user-play-hand">
                {suitOrder.map(suit => {
                  const suitCards = sortCards(handCards.filter(card => card.suit === suit));
                  return (
                    <div key={suit} className="suit-group">
                      {suitCards.map((card, index) => {
                        const isLegalCard = isCardLegalToPlay(card, handCards, current_trick);
                        const isDisabled = !isUserTurn || !isLegalCard;
                        return (
                          <PlayableCard
                            key={`user-${card.rank}-${card.suit}`}
                            card={card}
                            onClick={onCardPlay}
                            disabled={isDisabled}
                          />
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </div>

      </div>

      {/* Action Bar - Below play area */}
      <div className="action-bar">
        <div className="action-btns">
          {lastTrick && !isHandComplete && (
            <button
              className="action-btn secondary"
              onClick={showLastTrick ? onHideLastTrick : onShowLastTrick}
            >
              {showLastTrick ? 'Current Trick' : '↶ Last Trick'}
            </button>
          )}
        </div>
        <div className="action-status">
          {/* Status text can go here if needed */}
        </div>
      </div>
    </div>
  );
}

/**
 * Display final score after 13 tricks
 * MIGRATED: Now uses ScoreModal component from components/play/
 * Note: sessionData prop removed - cumulative scores now shown in separate panel
 */
export function ScoreDisplay({ scoreData, onClose, onDealNewHand, onShowLearningDashboard, onPlayAnotherHand, onReplayHand, onReviewHand }) {
  return <ScoreModal isOpen={!!scoreData} onClose={onClose} scoreData={scoreData} onDealNewHand={onDealNewHand} onShowLearningDashboard={onShowLearningDashboard} onPlayAnotherHand={onPlayAnotherHand} onReplayHand={onReplayHand} onReviewHand={onReviewHand} />;
}

// Export CompactTurnIndicator for use in other files
export { CompactTurnIndicator };
