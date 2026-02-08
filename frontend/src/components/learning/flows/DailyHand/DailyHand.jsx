/**
 * DailyHand.jsx
 *
 * Daily Hand Challenge Flow - One hand per day with streak tracking.
 * Reference: docs/redesign/Learning/learning-flows-package/docs/LEARNING_DESIGN_SYSTEM.md
 *
 * Flow States: DEAL -> BID -> PLAY -> RESULT -> SUMMARY
 */

import React, { useReducer, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

// Shared components
import {
  FlowLayout,
  HandDisplay,
  BidTable,
  ResultStrip,
  ScoreRow,
  StreakCalendar,
  PrimaryButton,
  SecondaryButton,
} from '../../shared';

// Local logic
import {
  FLOW_STATES,
  BID_LEVELS,
  STRAINS,
  STRAIN_SYMBOLS,
  getTodayString,
  getInitialState,
  dailyHandReducer,
  generateStreakCalendar,
  getCurrentBidder,
  getLegalBids,
  getAIBid,
  calculateHCP,
  saveDailyStorage,
  calculateNewStreak,
  buildFlowResult,
} from './DailyHand.logic';

import './DailyHand.css';

/**
 * BiddingBox Component - Renders the bidding interface
 */
const BiddingBox = ({
  selectedLevel,
  selectedStrain,
  legalBids,
  onSelectLevel,
  onSelectStrain,
  onBid,
  disabled,
}) => {
  const canMakeBid = selectedLevel && selectedStrain;
  const currentBid = canMakeBid ? `${selectedLevel}${selectedStrain}` : null;
  const isBidLegal = currentBid && legalBids.has(currentBid);

  const handleBidClick = () => {
    if (isBidLegal) {
      onBid(currentBid);
    }
  };

  const handlePassClick = () => {
    onBid('Pass');
  };

  const handleDoubleClick = () => {
    if (legalBids.has('X')) {
      onBid('X');
    }
  };

  const handleRedoubleClick = () => {
    if (legalBids.has('XX')) {
      onBid('XX');
    }
  };

  return (
    <div className="bidding-box">
      {/* Level buttons */}
      <div className="bidding-box-section">
        <div className="bidding-box-label">Level</div>
        <div className="level-buttons">
          {BID_LEVELS.map((level) => {
            // Check if any bid at this level is legal
            const anyLegal = STRAINS.some((s) => legalBids.has(`${level}${s}`));
            return (
              <button
                key={level}
                type="button"
                className={`level-button ${selectedLevel === level ? 'selected' : ''} ${!anyLegal ? 'disabled' : ''}`}
                onClick={() => anyLegal && onSelectLevel(level)}
                disabled={disabled || !anyLegal}
                aria-pressed={selectedLevel === level}
              >
                {level}
              </button>
            );
          })}
        </div>
      </div>

      {/* Strain buttons */}
      <div className="bidding-box-section">
        <div className="bidding-box-label">Suit</div>
        <div className="strain-buttons">
          {STRAINS.map((strain) => {
            const bid = selectedLevel ? `${selectedLevel}${strain}` : null;
            const isLegal = bid && legalBids.has(bid);
            const strainClass =
              strain === 'C'
                ? 'clubs'
                : strain === 'D'
                ? 'diamonds'
                : strain === 'H'
                ? 'hearts'
                : strain === 'S'
                ? 'spades'
                : 'notrump';

            return (
              <button
                key={strain}
                type="button"
                className={`suit-button ${strainClass} ${selectedStrain === strain ? 'selected' : ''} ${!isLegal ? 'disabled' : ''}`}
                onClick={() => isLegal && onSelectStrain(strain)}
                disabled={disabled || !selectedLevel || !isLegal}
                aria-pressed={selectedStrain === strain}
                aria-label={strain === 'NT' ? 'No Trump' : `${strainClass}`}
              >
                {STRAIN_SYMBOLS[strain]}
              </button>
            );
          })}
        </div>
      </div>

      {/* Action buttons */}
      <div className="bidding-box-actions">
        <button
          type="button"
          className="action-button pass-button"
          onClick={handlePassClick}
          disabled={disabled}
        >
          Pass
        </button>
        <button
          type="button"
          className={`action-button double-button ${!legalBids.has('X') ? 'disabled' : ''}`}
          onClick={handleDoubleClick}
          disabled={disabled || !legalBids.has('X')}
        >
          Dbl
        </button>
        <button
          type="button"
          className={`action-button redouble-button ${!legalBids.has('XX') ? 'disabled' : ''}`}
          onClick={handleRedoubleClick}
          disabled={disabled || !legalBids.has('XX')}
        >
          Rdbl
        </button>
        <PrimaryButton
          onClick={handleBidClick}
          disabled={disabled || !isBidLegal}
        >
          Bid {currentBid ? `${selectedLevel}${STRAIN_SYMBOLS[selectedStrain]}` : ''}
        </PrimaryButton>
      </div>
    </div>
  );
};

BiddingBox.propTypes = {
  selectedLevel: PropTypes.number,
  selectedStrain: PropTypes.string,
  legalBids: PropTypes.instanceOf(Set).isRequired,
  onSelectLevel: PropTypes.func.isRequired,
  onSelectStrain: PropTypes.func.isRequired,
  onBid: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};

/**
 * HandInfo Component - Shows HCP, dealer, vulnerability
 */
const HandInfo = ({ hcp, dealer, vulnerability }) => (
  <div className="hand-info">
    <div className="hand-info-item">
      <span className="hand-info-label">HCP</span>
      <span className="hand-info-value">{hcp}</span>
    </div>
    <div className="hand-info-item">
      <span className="hand-info-label">Dealer</span>
      <span className="hand-info-value">{dealer}</span>
    </div>
    <div className="hand-info-item">
      <span className="hand-info-label">Vul</span>
      <span className="hand-info-value">{vulnerability}</span>
    </div>
  </div>
);

HandInfo.propTypes = {
  hcp: PropTypes.number.isRequired,
  dealer: PropTypes.string.isRequired,
  vulnerability: PropTypes.string.isRequired,
};

/**
 * PlayArea Component - Shows the play table (placeholder)
 * TODO: Implement full play table with trick display
 */
const PlayArea = ({ currentTrick, tricksPlayed, tricksTaken, contract }) => (
  <div className="play-area">
    <div className="play-area-header">
      <span className="contract-display">
        Contract: {contract.level}
        {STRAIN_SYMBOLS[contract.strain]} by {contract.declarer}
        {contract.doubled && ' X'}
        {contract.redoubled && ' XX'}
      </span>
    </div>
    <div className="trick-display">
      {/* TODO: Render current trick cards */}
      <div className="trick-placeholder">
        Trick {tricksPlayed + 1} / 13
      </div>
    </div>
    <div className="tricks-count">
      <span>NS: {tricksTaken.NS}</span>
      <span>EW: {tricksTaken.EW}</span>
    </div>
  </div>
);

PlayArea.propTypes = {
  currentTrick: PropTypes.array.isRequired,
  tricksPlayed: PropTypes.number.isRequired,
  tricksTaken: PropTypes.shape({
    NS: PropTypes.number,
    EW: PropTypes.number,
  }).isRequired,
  contract: PropTypes.shape({
    level: PropTypes.number,
    strain: PropTypes.string,
    declarer: PropTypes.string,
    doubled: PropTypes.bool,
    redoubled: PropTypes.bool,
  }).isRequired,
};

/**
 * DailyHand Main Component
 */
function DailyHand({ onClose = null, onComplete = null }) {
  const dateString = getTodayString();

  // Initialize state
  const [state, dispatch] = useReducer(dailyHandReducer, dateString, getInitialState);

  // Destructure state
  const {
    flowState,
    allHands,
    dealer,
    vulnerability,
    auction,
    contract,
    currentTrick,
    tricksPlayed,
    tricksTaken,
    ddsOptimal,
    startTime,
    // isCompleted is handled by initial state -> SUMMARY flow
    streak,
    selectedLevel,
    selectedStrain,
  } = state;

  // Player is always South
  const playerHand = allHands.south;
  const playerHCP = useMemo(() => calculateHCP(playerHand), [playerHand]);

  // Current bidder
  const currentBidder = useMemo(
    () => getCurrentBidder(auction, dealer),
    [auction, dealer]
  );
  const isPlayerTurn = currentBidder === 'S';

  // Legal bids
  const legalBids = useMemo(() => getLegalBids(auction), [auction]);

  // Streak calendar data
  const streakDays = useMemo(() => generateStreakCalendar(), []);

  // AI bidding effect
  useEffect(() => {
    if (flowState !== FLOW_STATES.BID) return;
    if (isPlayerTurn) return;

    // AI takes a turn after a short delay
    const timer = setTimeout(() => {
      const aiHand =
        currentBidder === 'N'
          ? allHands.north
          : currentBidder === 'E'
          ? allHands.east
          : allHands.west;

      const { bid, explanation } = getAIBid(aiHand, auction, currentBidder);
      dispatch({
        type: 'MAKE_BID',
        payload: { bid, bidder: currentBidder, explanation },
      });
    }, 500);

    return () => clearTimeout(timer);
  }, [flowState, currentBidder, isPlayerTurn, allHands, auction]);

  // Handle player bid
  const handlePlayerBid = useCallback(
    (bid) => {
      dispatch({
        type: 'MAKE_BID',
        payload: { bid, bidder: 'S', explanation: 'User bid' },
      });
    },
    []
  );

  // Handle level selection
  const handleSelectLevel = useCallback((level) => {
    dispatch({ type: 'SELECT_LEVEL', payload: level });
  }, []);

  // Handle strain selection
  const handleSelectStrain = useCallback((strain) => {
    dispatch({ type: 'SELECT_STRAIN', payload: strain });
  }, []);

  // Handle start bidding
  const handleStartBidding = useCallback(() => {
    dispatch({ type: 'START_BIDDING' });
  }, []);

  // Handle result -> summary transition
  const handleShowSummary = useCallback(() => {
    // Calculate results and save
    const declarerSide = contract?.declarer === 'N' || contract?.declarer === 'S' ? 'NS' : 'EW';
    const tricksMade = tricksTaken[declarerSide];
    const requiredTricks = contract ? 6 + contract.level : 0;
    const tricksVsOptimal = tricksMade - (ddsOptimal || 0);

    const newStreak = calculateNewStreak(dateString);
    const timeSpent = Date.now() - startTime;

    // Save to localStorage
    saveDailyStorage({
      date: dateString,
      result: { tricksMade, required: requiredTricks, optimal: ddsOptimal },
      streak: newStreak,
      completedAt: new Date().toISOString(),
    });

    // Build and emit flow result
    const flowResult = buildFlowResult({
      dateString,
      decisions: [], // TODO: Track individual decisions
      tricksVsOptimal,
      timeSpent,
    });

    if (onComplete) {
      onComplete(flowResult);
    }

    dispatch({ type: 'COMPLETE_DAILY', payload: { streak: newStreak } });
    dispatch({ type: 'SHOW_SUMMARY' });
  }, [contract, tricksTaken, ddsOptimal, dateString, startTime, onComplete]);

  // Auto-progress play (placeholder - TODO: implement real play)
  useEffect(() => {
    if (flowState !== FLOW_STATES.PLAY) return;

    // For now, simulate completing play after a delay
    // TODO: Implement actual card play with AI
    const timer = setTimeout(() => {
      // Simulate a result
      handleShowSummary();
    }, 2000);

    return () => clearTimeout(timer);
  }, [flowState, handleShowSummary]);

  // Get step indicator text
  const getStepIndicator = () => {
    switch (flowState) {
      case FLOW_STATES.DEAL:
        return 'Step 1 of 4: Review Hand';
      case FLOW_STATES.BID:
        return 'Step 2 of 4: Bidding';
      case FLOW_STATES.PLAY:
        return 'Step 3 of 4: Play';
      case FLOW_STATES.RESULT:
        return 'Step 4 of 4: Result';
      case FLOW_STATES.SUMMARY:
        return 'Complete';
      default:
        return '';
    }
  };

  // Render felt zone content based on state
  const renderFeltContent = () => {
    switch (flowState) {
      case FLOW_STATES.DEAL:
        return (
          <div className="deal-felt-content">
            <HandInfo
              hcp={playerHCP}
              dealer={dealer}
              vulnerability={vulnerability}
            />
            <HandDisplay cards={playerHand} mode="hand-h" />
          </div>
        );

      case FLOW_STATES.BID:
        return (
          <div className="bid-felt-content">
            <HandInfo
              hcp={playerHCP}
              dealer={dealer}
              vulnerability={vulnerability}
            />
            <div className="bid-felt-layout">
              <div className="bid-table-container">
                <BidTable
                  bids={auction}
                  dealer={dealer}
                  playerSeat="S"
                />
              </div>
              <HandDisplay cards={playerHand} mode="hand-h" />
            </div>
          </div>
        );

      case FLOW_STATES.PLAY:
        return (
          <div className="play-felt-content">
            <PlayArea
              currentTrick={currentTrick}
              tricksPlayed={tricksPlayed}
              tricksTaken={tricksTaken}
              contract={contract}
            />
            <HandDisplay
              cards={playerHand}
              mode="hand-h"
              selectable={false} // TODO: Enable when implementing play
            />
          </div>
        );

      case FLOW_STATES.RESULT:
      case FLOW_STATES.SUMMARY:
        return null;

      default:
        return null;
    }
  };

  // Render interaction zone content based on state
  const renderInteractionContent = () => {
    switch (flowState) {
      case FLOW_STATES.DEAL:
        return (
          <div className="deal-interaction-content">
            <div className="streak-section">
              <div className="panel-label">Your Streak</div>
              <StreakCalendar days={streakDays} />
              <div className="streak-count">
                Current streak: <strong>{streak}</strong> day{streak !== 1 ? 's' : ''}
              </div>
            </div>
            <PrimaryButton onClick={handleStartBidding}>
              Start Bidding
            </PrimaryButton>
          </div>
        );

      case FLOW_STATES.BID:
        return (
          <div className="bid-interaction-content">
            {isPlayerTurn ? (
              <BiddingBox
                selectedLevel={selectedLevel}
                selectedStrain={selectedStrain}
                legalBids={legalBids}
                onSelectLevel={handleSelectLevel}
                onSelectStrain={handleSelectStrain}
                onBid={handlePlayerBid}
                disabled={false}
              />
            ) : (
              <div className="waiting-message">
                Waiting for {currentBidder} to bid...
              </div>
            )}
          </div>
        );

      case FLOW_STATES.PLAY:
        return (
          <div className="play-interaction-content">
            <div className="play-prompt">
              {/* TODO: Show whose turn and prompt for card selection */}
              Playing hand... (simulated)
            </div>
          </div>
        );

      case FLOW_STATES.RESULT: {
        const declarerSide = contract?.declarer === 'N' || contract?.declarer === 'S' ? 'NS' : 'EW';
        const tricksMade = tricksTaken[declarerSide];
        const requiredTricks = contract ? 6 + contract.level : 0;
        const madeContract = tricksMade >= requiredTricks;

        return (
          <div className="result-interaction-content">
            <ResultStrip
              type={madeContract ? 'success' : 'error'}
              message={madeContract ? 'Contract Made!' : 'Contract Failed'}
              detail={`${tricksMade} tricks (needed ${requiredTricks})`}
            />
            <div className="result-scores">
              <ScoreRow
                label="Tricks Made"
                value={tricksMade}
                status={madeContract ? 'good' : 'bad'}
              />
              <ScoreRow
                label="DDS Optimal"
                value={ddsOptimal}
                status="neutral"
              />
              <ScoreRow
                label="Difference"
                value={tricksMade - ddsOptimal >= 0 ? `+${tricksMade - ddsOptimal}` : tricksMade - ddsOptimal}
                status={tricksMade >= ddsOptimal ? 'good' : 'bad'}
              />
            </div>
            <PrimaryButton onClick={handleShowSummary}>
              Continue
            </PrimaryButton>
          </div>
        );
      }

      case FLOW_STATES.SUMMARY:
        return (
          <div className="summary-interaction-content">
            <div className="summary-header">
              <div className="summary-title">Daily Challenge Complete!</div>
            </div>
            <div className="streak-section">
              <div className="panel-label">Your Streak</div>
              <StreakCalendar days={generateStreakCalendar()} />
              <div className="streak-count streak-updated">
                Streak: <strong>{streak}</strong> day{streak !== 1 ? 's' : ''}
              </div>
            </div>
            <div className="summary-message">
              Come back tomorrow for your next hand!
            </div>
            <SecondaryButton onClick={onClose}>
              Back to Dashboard
            </SecondaryButton>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <FlowLayout
      title="Daily Hand Challenge"
      stepIndicator={getStepIndicator()}
      onClose={onClose}
      feltContent={renderFeltContent()}
      interactionContent={renderInteractionContent()}
    />
  );
}

DailyHand.propTypes = {
  onClose: PropTypes.func,
  onComplete: PropTypes.func,
};

export default DailyHand;
