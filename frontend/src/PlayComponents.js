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
import { PlayableCard as PlayableCardComponent } from './components/play/PlayableCard';
import { VerticalPlayableCard } from './components/play/VerticalPlayableCard';
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
  onReplay
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
  // Pass dummy_revealed from playState to ensure dummy is only shown AFTER opening lead
  const dummyRevealed = playState.dummy_revealed || false;
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
      <ContractHeader contract={contract} tricksWon={tricks_won} auction={auction} dealer={dealer} scoreData={scoreData} vulnerability={vulnerability} />

      <div className="play-area">
        {/* North position */}
        <div className="position position-north">
          {/* Position label with badges per UI Redesign Spec */}
          <div className={`position-label ${next_to_play === 'N' ? 'active-turn' : ''}`}>
            North
            {dummyPosition === 'N' && <span className="position-badge dummy">Dummy</span>}
            {declarerPosition === 'N' && <span className="position-badge declarer">Declarer</span>}
            {dummyPosition === 'N' && userIsDeclarer && <span className="position-badge you-control">You Control</span>}
          </div>
          {/* CRITICAL: Use centralized visibility rule - prevents regression bugs */}
          {showNorthHand && !isHandComplete && (
            <div className={dummyPosition === 'N' ? "dummy-hand" : "declarer-hand"}>
              {suitOrder.map(suit => {
                const hand = dummyPosition === 'N' ? dummyHand : declarerHand;
                if (!hand || hand.length === 0) return null;
                const suitCards = sortCards(hand.filter(card => card.suit === suit));
                return (
                  <div key={suit} className="suit-group">
                    {suitCards.map((card, index) => {
                      // CRITICAL: Determine if this specific card is legal to play
                      const isMyTurn = dummyPosition === 'N' ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn;
                      const isLegalCard = isCardLegalToPlay(card, hand, current_trick);
                      const isDisabled = !isMyTurn || !isLegalCard;

                      // CRITICAL: Use unique key across ALL cards (not just within suit)
                      const cardKey = `north-${card.rank}-${card.suit}`;

                      return (
                        <PlayableCard
                          key={cardKey}
                          card={card}
                          onClick={dummyPosition === 'N' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                          disabled={isDisabled}
                        />
                      );
                    })}
                  </div>
                );
              })}
            </div>
          )}
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


        {/* West position - Left side (standard bridge layout) */}
        <div className="position position-west">
          <div className={`position-label ${next_to_play === 'W' ? 'active-turn' : ''}`}>
            West
            {dummyPosition === 'W' && <span className="position-badge dummy">Dummy</span>}
            {declarerPosition === 'W' && <span className="position-badge declarer">Declarer</span>}
            {dummyPosition === 'W' && userIsDeclarer && <span className="position-badge you-control">You Control</span>}
          </div>
          {/* CRITICAL: Use centralized visibility rule - prevents regression bugs */}
          {showWestHand && !isHandComplete ? (
            <div className={dummyPosition === 'W' ? "dummy-hand" : "declarer-hand"}>
              {suitOrder.map(suit => {
                const hand = dummyPosition === 'W' ? dummyHand : declarerHand;
                if (!hand || hand.length === 0) return null;
                const suitCards = sortCards(hand.filter(card => card.suit === suit));
                return (
                  <div key={suit} className="suit-group">
                    {suitCards.map((card, index) => {
                      // CRITICAL: Determine if this specific card is legal to play
                      const isMyTurn = dummyPosition === 'W' ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn;
                      const isLegalCard = isCardLegalToPlay(card, hand, current_trick);
                      const isDisabled = !isMyTurn || !isLegalCard;

                      // CRITICAL: Use unique key per card
                      const cardKey = `west-${card.rank}-${card.suit}`;

                      return (
                        <VerticalPlayableCard
                          key={cardKey}
                          card={card}
                          onClick={dummyPosition === 'W' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                          disabled={isDisabled}
                        />
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ) : !isHandComplete && (
            /* Show card backs when hand is hidden */
            <div className="opponent-display">
              <div className="opponent-card-fan">
                {Array.from({ length: Math.min(6, 13 - totalTricksPlayed) }).map((_, i) => (
                  <div key={i} className="card-back" />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* East position - Right side (standard bridge layout) */}
        <div className="position position-east">
          <div className={`position-label ${next_to_play === 'E' ? 'active-turn' : ''}`}>
            East
            {dummyPosition === 'E' && <span className="position-badge dummy">Dummy</span>}
            {declarerPosition === 'E' && <span className="position-badge declarer">Declarer</span>}
            {dummyPosition === 'E' && userIsDeclarer && <span className="position-badge you-control">You Control</span>}
          </div>
          {/* CRITICAL: Use centralized visibility rule - prevents regression bugs */}
          {showEastHand && !isHandComplete ? (
            <div className={dummyPosition === 'E' ? "dummy-hand" : "declarer-hand"}>
              {suitOrder.map(suit => {
                const hand = dummyPosition === 'E' ? dummyHand : declarerHand;
                if (!hand || hand.length === 0) return null;
                const suitCards = sortCards(hand.filter(card => card.suit === suit));
                return (
                  <div key={suit} className="suit-group">
                    {suitCards.map((card, index) => {
                      // CRITICAL: Determine if this specific card is legal to play
                      const isMyTurn = dummyPosition === 'E' ? (userIsDeclarer && isDummyTurn) : isDeclarerTurn;
                      const isLegalCard = isCardLegalToPlay(card, hand, current_trick);
                      const isDisabled = !isMyTurn || !isLegalCard;

                      // CRITICAL: Use unique key per card
                      const cardKey = `east-${card.rank}-${card.suit}`;

                      return (
                        <VerticalPlayableCard
                          key={cardKey}
                          card={card}
                          onClick={dummyPosition === 'E' && userIsDeclarer ? onDummyCardPlay : onDeclarerCardPlay}
                          disabled={isDisabled}
                        />
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ) : !isHandComplete && (
            /* Show card backs when hand is hidden */
            <div className="opponent-display">
              <div className="opponent-card-fan">
                {Array.from({ length: Math.min(6, 13 - totalTricksPlayed) }).map((_, i) => (
                  <div key={i} className="card-back" />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* South position (user) */}
        <div className="position position-south">
          <div className={`position-label ${(next_to_play === 'S' && !userIsDummy) ? 'active-turn' : ''}`}>
            South (You)
            {userIsDummy && <span className="position-badge dummy">Dummy</span>}
            {userIsDeclarer && <span className="position-badge declarer">Declarer</span>}
          </div>
          {userHand && userHand.length > 0 && (
            <div className="user-play-hand">
              {suitOrder.map(suit => {
                const suitCards = sortCards(userHand.filter(card => card.suit === suit));
                return (
                  <div key={suit} className="suit-group">
                    {suitCards.map((card, index) => {
                      // CRITICAL: Determine if this specific card is legal to play
                      const isLegalCard = isCardLegalToPlay(card, userHand, current_trick);
                      const isDisabled = !isUserTurn || !isLegalCard;

                      // CRITICAL: Use unique key per card
                      const cardKey = `south-${card.rank}-${card.suit}`;

                      return (
                        <PlayableCard
                          key={cardKey}
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
          )}
        </div>
      </div>

      {/* Turn Indicator - centered below table per mockup */}
      {!isHandComplete && (
        <div className="play-turn-indicator">
          <span className="turn-dot" />
          {trick_complete ? (
            <span className="turn-text">
              {(trick_winner === 'N' || trick_winner === 'S') ? 'You win' : (trick_winner === 'E' ? 'East' : 'West') + ' wins'} — click to collect trick
            </span>
          ) : (isUserTurn || (userIsDeclarer && isDummyTurn)) ? (
            <span className="turn-text">
              Your turn — {dummyPosition && next_to_play === dummyPosition ? 'play from dummy' : 'click a card to play'}
            </span>
          ) : (
            <span className="turn-text">
              Waiting for {next_to_play === 'N' ? 'North' : next_to_play === 'E' ? 'East' : next_to_play === 'S' ? 'South' : 'West'}...
            </span>
          )}
        </div>
      )}

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
              {showLastTrick ? 'Current' : '↶ Last Trick'}
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
