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
import { LastTrickOverlay } from './components/play/LastTrickOverlay';
import { ScoreModal } from './components/play/ScoreModal';
import PlayFeedbackPanel from './components/play/PlayFeedbackPanel';
import { PlayableCard as PlayableCardComponent } from './components/play/PlayableCard';
import { sortCards } from './shared/utils/cardUtils';
import Card from './shared/components/Card';
import TrickArena from './components/shared/TrickArena';
import ReactorLayout from './components/layout/ReactorLayout';

/**
 * PlayableSuitStack - Physics v2.0 compliant suit row for E/W positions
 * Renders a vertical stack of suit rows, each with em-based overlapping cards
 *
 * @param {Array} hand - Full hand of cards
 * @param {Array} suitOrder - Order of suits to display
 * @param {Array} currentTrick - Current trick for legality checking
 * @param {boolean} isMyTurn - Is it this position's turn?
 * @param {function} onCardPlay - Click handler for card plays
 * @param {string} positionKey - Position identifier for unique keys (e.g., 'east', 'west')
 * @param {string} scaleClass - Tailwind text scale class (e.g., 'text-sm')
 */
function PlayableSuitStack({ hand, suitOrder, currentTrick, isMyTurn, onCardPlay, positionKey, scaleClass = 'text-sm' }) {
  if (!hand || hand.length === 0) return null;

  // Helper to check if card is legal to play
  const isCardLegal = (card) => {
    if (!currentTrick || currentTrick.length === 0) return true;
    const ledSuit = currentTrick[0].card.suit;
    const hasLedSuit = hand.some(c => c.suit === ledSuit);
    if (hasLedSuit) return card.suit === ledSuit;
    return true;
  };

  // Dynamic spacing based on card count (matching SuitRow.jsx patterns)
  const getSpacingClass = (count) => {
    if (count >= 7) return '-space-x-[1.9em]';
    if (count === 6) return '-space-x-[1.6em]';
    if (count === 5) return '-space-x-[1.4em]';
    return '-space-x-[1.2em]';
  };

  return (
    <div className={`${scaleClass} flex flex-col gap-[0.3em]`}>
      {suitOrder.map(suit => {
        const suitCards = sortCards(hand.filter(card => card.suit === suit));
        if (suitCards.length === 0) return null;

        const spacingClass = getSpacingClass(suitCards.length);

        return (
          <div key={suit} className={`flex flex-row ${spacingClass}`}>
            {suitCards.map((card, idx) => {
              const isLegalCard = isCardLegal(card);
              const isDisabled = !isMyTurn || !isLegalCard;
              const cardKey = `${positionKey}-${card.rank}-${card.suit}`;

              return (
                <div key={cardKey} style={{ zIndex: 10 + idx }}>
                  <Card
                    rank={card.rank}
                    suit={card.suit}
                    customScaleClass={scaleClass}
                    selectable={!isDisabled}
                    onClick={!isDisabled ? () => onCardPlay(card) : undefined}
                  />
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

/**
 * PlayableHorizontalHand - Physics v2.0 compliant horizontal hand for N/S positions
 * Renders horizontal suit groups with overlapping cards
 * Used for both North and South (faces user horizontally)
 *
 * @param {string} positionKey - 'north' or 'south' for unique keys
 */
function PlayableHorizontalHand({ hand, suitOrder, currentTrick, isMyTurn, onCardPlay, positionKey, scaleClass = 'text-base' }) {
  if (!hand || hand.length === 0) return null;

  // Helper to check if card is legal to play
  const isCardLegal = (card) => {
    if (!currentTrick || currentTrick.length === 0) return true;
    const ledSuit = currentTrick[0].card.suit;
    const hasLedSuit = hand.some(c => c.suit === ledSuit);
    if (hasLedSuit) return card.suit === ledSuit;
    return true;
  };

  // Dynamic spacing based on scale (tighter for smaller cards)
  const getSpacingClass = (count) => {
    if (count >= 7) return '-space-x-[2.2em]';
    if (count === 6) return '-space-x-[1.9em]';
    if (count === 5) return '-space-x-[1.6em]';
    return '-space-x-[1.4em]';
  };

  return (
    <div className={`${scaleClass} flex flex-row gap-[0.8em] justify-center`}>
      {suitOrder.map(suit => {
        const suitCards = sortCards(hand.filter(card => card.suit === suit));
        if (suitCards.length === 0) return null;

        const spacingClass = getSpacingClass(suitCards.length);

        return (
          <div key={suit} className={`flex flex-row ${spacingClass}`}>
            {suitCards.map((card, idx) => {
              const isLegalCard = isCardLegal(card);
              const isDisabled = !isMyTurn || !isLegalCard;
              const cardKey = `${positionKey}-${card.rank}-${card.suit}`;

              return (
                <div key={cardKey} style={{ zIndex: 10 + idx }}>
                  <Card
                    rank={card.rank}
                    suit={card.suit}
                    customScaleClass={scaleClass}
                    selectable={!isDisabled}
                    onClick={!isDisabled ? () => onCardPlay(card) : undefined}
                  />
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

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
function shouldShowHand(position, dummyPosition, declarerPosition, userIsDummy, dummyRevealed) {
  // Rule 1: Always show South (user's own hand)
  if (position === 'S') {
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
  vulnerability,
  // Last trick feature props
  showLastTrick,
  lastTrick,
  onShowLastTrick,
  onHideLastTrick,
  // Action bar props
  onNewHand,
  onUndo,
  onReplay,
  onClaim  // Claim remaining tricks
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

  // Calculate tricks played first (needed for multiple purposes including dummy visibility)
  const totalTricksPlayed = Object.values(tricks_won).reduce((sum, tricks) => sum + tricks, 0);

  // CRITICAL FIX: Dummy is revealed after opening lead
  // Infer from game state if backend doesn't provide it:
  // - Any card in current trick means opening lead was made
  // - Any completed tricks means play has progressed past opening lead
  const dummyRevealed = playState.dummy_revealed === true ||
                        (current_trick && current_trick.length > 0) ||
                        totalTricksPlayed > 0;

  // CRITICAL: Centralized visibility rules - USE THESE for all hand rendering
  const showNorthHand = shouldShowHand('N', dummyPosition, declarerPosition, userIsDummy, dummyRevealed);
  const showEastHand = shouldShowHand('E', dummyPosition, declarerPosition, userIsDummy, dummyRevealed);
  const showSouthHand = shouldShowHand('S', dummyPosition, declarerPosition, userIsDummy, dummyRevealed);
  const showWestHand = shouldShowHand('W', dummyPosition, declarerPosition, userIsDummy, dummyRevealed);

  // DEBUG: Log visibility decisions
  console.log('👁️ Hand Visibility Rules Applied:', {
    dummyPosition,
    declarerPosition,
    userIsDummy,
    userIsDeclarer,
    dummyRevealed,  // CRITICAL: Track if dummy should be visible
    visibility: {
      'North': showNorthHand,
      'East': showEastHand,
      'South': showSouthHand,
      'West': showWestHand
    },
    reason: {
      'North': showNorthHand ? (dummyPosition === 'N' ? `DUMMY (revealed: ${dummyRevealed})` : userIsDummy && declarerPosition === 'N' ? 'DECLARER (user controls)' : 'UNKNOWN') : 'HIDDEN',
      'East': showEastHand ? (dummyPosition === 'E' ? `DUMMY (revealed: ${dummyRevealed})` : userIsDummy && declarerPosition === 'E' ? 'DECLARER (user controls)' : 'UNKNOWN') : 'HIDDEN',
      'South': 'USER (always visible)',
      'West': showWestHand ? (dummyPosition === 'W' ? `DUMMY (revealed: ${dummyRevealed})` : userIsDummy && declarerPosition === 'W' ? 'DECLARER (user controls)' : 'UNKNOWN') : 'HIDDEN'
    }
  });

  // Calculate tricks for consolidated header (totalTricksPlayed already calculated above)
  const tricksNeeded = contract.level + 6;
  const declarerSide = (declarerPosition === 'N' || declarerPosition === 'S') ? 'NS' : 'EW';
  const tricksWonBySide = declarerSide === 'NS'
    ? (tricks_won.N || 0) + (tricks_won.S || 0)
    : (tricks_won.E || 0) + (tricks_won.W || 0);
  const tricksRemaining = 13 - totalTricksPlayed;
  const tricksLost = 13 - tricksWonBySide - tricksRemaining;

  // Check if hand is complete
  const isHandComplete = totalTricksPlayed === 13;

  return (
    <div className="play-table">
      {/* Consolidated Contract Header - MIGRATED to ContractHeader component */}
      <ContractHeader contract={contract} tricksWon={tricks_won} auction={auction} dealer={dealer} scoreData={scoreData} vulnerability={vulnerability} />

      {/* ReactorLayout: Centripetal 3x3 Grid - Physics v2.0 */}
      <ReactorLayout
        className="play-area reactor-layout"
        scaleClass="text-base"
        north={
          <div className="position-orbit position-north-orbit">
            <div className={`position-label ${next_to_play === 'N' ? 'active-turn' : ''}`}>
              North
              {dummyPosition === 'N' && <span className="position-badge dummy">Dummy</span>}
              {declarerPosition === 'N' && <span className="position-badge declarer">Declarer</span>}
              {dummyPosition === 'N' && userIsDeclarer && <span className="position-badge you-control">You Control</span>}
            </div>
            {showNorthHand && !isHandComplete && (
              <PlayableHorizontalHand
                hand={dummyPosition === 'N' ? dummyHand : declarerHand}
                suitOrder={suitOrder}
                currentTrick={current_trick}
                isMyTurn={dummyPosition === 'N' ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn}
                onCardPlay={dummyPosition === 'N' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                positionKey="north"
                scaleClass="text-sm"
              />
            )}
          </div>
        }
        south={
          <div className="position-orbit position-south-orbit">
            <div className={`position-label ${(next_to_play === 'S' && !userIsDummy) ? 'active-turn' : ''}`}>
              South (You)
              {userIsDummy && <span className="position-badge dummy">Dummy</span>}
              {userIsDeclarer && <span className="position-badge declarer">Declarer</span>}
            </div>
            {userHand && userHand.length > 0 && (
              <PlayableHorizontalHand
                hand={userHand}
                suitOrder={suitOrder}
                currentTrick={current_trick}
                isMyTurn={isUserTurn}
                onCardPlay={onCardPlay}
                positionKey="south"
                scaleClass="text-lg"
              />
            )}
          </div>
        }
        east={
          <div className="position-orbit position-east-orbit">
            <div className={`position-label ${next_to_play === 'E' ? 'active-turn' : ''}`}>
              East
              {dummyPosition === 'E' && <span className="position-badge dummy">Dummy</span>}
              {declarerPosition === 'E' && <span className="position-badge declarer">Declarer</span>}
              {dummyPosition === 'E' && userIsDeclarer && <span className="position-badge you-control">You Control</span>}
            </div>
            {showEastHand && !isHandComplete ? (
              <PlayableSuitStack
                hand={dummyPosition === 'E' ? dummyHand : declarerHand}
                suitOrder={suitOrder}
                currentTrick={current_trick}
                isMyTurn={dummyPosition === 'E' ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn}
                onCardPlay={dummyPosition === 'E' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                positionKey="east"
                scaleClass="text-sm"
              />
            ) : !isHandComplete && (
              <div className="opponent-display compact">
                <div className="card-back-single" />
                <span className="opp-count">{13 - totalTricksPlayed}</span>
              </div>
            )}
          </div>
        }
        west={
          <div className="position-orbit position-west-orbit">
            <div className={`position-label ${next_to_play === 'W' ? 'active-turn' : ''}`}>
              West
              {dummyPosition === 'W' && <span className="position-badge dummy">Dummy</span>}
              {declarerPosition === 'W' && <span className="position-badge declarer">Declarer</span>}
              {dummyPosition === 'W' && userIsDeclarer && <span className="position-badge you-control">You Control</span>}
            </div>
            {showWestHand && !isHandComplete ? (
              <PlayableSuitStack
                hand={dummyPosition === 'W' ? dummyHand : declarerHand}
                suitOrder={suitOrder}
                currentTrick={current_trick}
                isMyTurn={dummyPosition === 'W' ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn}
                onCardPlay={dummyPosition === 'W' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                positionKey="west"
                scaleClass="text-sm"
              />
            ) : !isHandComplete && (
              <div className="opponent-display compact">
                <div className="card-back-single" />
                <span className="opp-count">{13 - totalTricksPlayed}</span>
              </div>
            )}
          </div>
        }
        center={
          <>
            {showLastTrick && lastTrick ? (
              <LastTrickOverlay
                trick={lastTrick}
                trickNumber={playState.trick_history?.length || 0}
                onClose={onHideLastTrick}
              />
            ) : (
              <TrickArena
                playedCards={(() => {
                  const cards = {};
                  (current_trick || []).forEach(({ card, position }) => {
                    if (card && position) {
                      cards[position] = {
                        rank: card.rank,
                        suit: card.suit,
                        isWinner: trick_complete && trick_winner === position
                      };
                    }
                  });
                  return cards;
                })()}
                scaleClass="text-base"
              />
            )}
          </>
        }
      />

      {/* Bottom Action Bar - slim row per mockup */}
      <div className="action-bar">
        <div className="action-btns">
          {onNewHand && (
            <button className="action-btn primary" onClick={onNewHand}>
              🎲 New Hand
            </button>
          )}
          {onUndo && (
            <button className="action-btn secondary" onClick={onUndo}>
              ↩ Undo
            </button>
          )}
          {lastTrick && !isHandComplete && (
            <button
              className="action-btn secondary"
              onClick={showLastTrick ? onHideLastTrick : onShowLastTrick}
            >
              {showLastTrick ? '◆ Current' : '↶ Last Trick'}
            </button>
          )}
          {onClaim && !isHandComplete && userIsDeclarer && totalTricksPlayed > 0 && (
            <button
              className="action-btn secondary"
              onClick={onClaim}
            >
              🏆 Claim
            </button>
          )}
          {onReplay && (
            <button className="action-btn secondary" onClick={onReplay}>
              🔄 Replay
            </button>
          )}
        </div>
        {/* Trump and Trick info removed - already shown in ContractHeader */}
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

// Export TurnIndicator components for use in other files
export { TurnIndicator, CompactTurnIndicator };

// Export PlayFeedbackPanel for inline play result feedback
export { PlayFeedbackPanel };
