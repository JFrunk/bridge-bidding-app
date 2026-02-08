/**
 * OpeningLead.jsx
 *
 * Flow 2: Opening Lead Quiz
 *
 * A learning flow that tests the player's ability to select the correct
 * opening lead. Uses DDS (Double Dummy Solver) analysis to evaluate leads.
 *
 * Flow states: PRESENT -> SELECT -> EVALUATE -> RESULT
 */

import React, { useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

// Shared components
import {
  FlowLayout,
  HandDisplay,
  BidTable,
  ResultStrip,
  PrimaryButton
} from '../../shared';

// Local imports
import { MOCK_HANDS } from './mockData';
import {
  FLOW_STATES,
  evaluateLead,
  getLeadComparison,
  getLeaderName,
  createFlowResult,
  getResultMessage,
  cardsEqual
} from './OpeningLead.logic';
import { SUIT_SYMBOLS, isRedSuit, sortCards } from '../../types/hand-types';

// Styles
import './OpeningLead.css';

/**
 * LeadCompareTable - Custom table for comparing lead options
 */
function LeadCompareTable({ leads, selectedCard, optimalCard }) {
  if (!leads || leads.length === 0) return null;

  return (
    <table className="lead-compare-table">
      <thead>
        <tr>
          <th>Lead Card</th>
          <th>Defensive Tricks</th>
          <th>Contract Result</th>
        </tr>
      </thead>
      <tbody>
        {leads.map((lead, index) => {
          const isPlayer = cardsEqual(lead.card, selectedCard);
          const isOptimal = cardsEqual(lead.card, optimalCard);
          const isRed = isRedSuit(lead.card.suit);
          const isDown = lead.contractResult.toLowerCase().includes('down');

          let rowClass = '';
          if (isOptimal) rowClass = 'optimal-choice';
          else if (isPlayer) rowClass = 'player-choice';

          return (
            <tr key={`${lead.card.rank}-${lead.card.suit}-${index}`} className={rowClass}>
              <td>
                <span className="lead-card-cell">
                  <span className="card-rank">{lead.card.rank}</span>
                  <span className={`card-suit ${isRed ? 'red' : 'black'}`}>
                    {SUIT_SYMBOLS[lead.card.suit]}
                  </span>
                </span>
                {isPlayer && !isOptimal && (
                  <span className="lead-player-indicator">(You)</span>
                )}
                {isOptimal && (
                  <span className="lead-optimal-indicator">(Best)</span>
                )}
              </td>
              <td className={`tricks-cell ${isOptimal ? 'good' : ''}`}>
                {lead.defensiveTricks}
              </td>
              <td className={`result-cell ${isDown ? 'down' : 'making'}`}>
                {lead.contractResult}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

LeadCompareTable.propTypes = {
  leads: PropTypes.arrayOf(PropTypes.shape({
    card: PropTypes.shape({
      rank: PropTypes.string.isRequired,
      suit: PropTypes.oneOf(['S', 'H', 'D', 'C']).isRequired
    }).isRequired,
    defensiveTricks: PropTypes.number.isRequired,
    contractResult: PropTypes.string.isRequired
  })).isRequired,
  selectedCard: PropTypes.shape({
    rank: PropTypes.string.isRequired,
    suit: PropTypes.oneOf(['S', 'H', 'D', 'C']).isRequired
  }),
  optimalCard: PropTypes.shape({
    rank: PropTypes.string.isRequired,
    suit: PropTypes.oneOf(['S', 'H', 'D', 'C']).isRequired
  })
};

/**
 * ContractBadge - Displays the contract with proper suit coloring
 */
function ContractBadge({ contract }) {
  const strainDisplay = {
    S: { symbol: '\u2660', isRed: false },
    H: { symbol: '\u2665', isRed: true },
    D: { symbol: '\u2666', isRed: true },
    C: { symbol: '\u2663', isRed: false },
    NT: { symbol: 'NT', isRed: false }
  };

  const strain = strainDisplay[contract.strain] || { symbol: contract.strain, isRed: false };
  const declarerNames = { N: 'North', E: 'East', S: 'South', W: 'West' };

  return (
    <div className="lead-contract-display">
      <div className="lead-contract-badge">
        <span>{contract.level}</span>
        <span className={`lead-contract-strain ${strain.isRed ? 'red' : 'black'}`}>
          {strain.symbol}
        </span>
        {contract.doubled && <span>X</span>}
        {contract.redoubled && <span>XX</span>}
      </div>
      <div className="lead-declarer">
        by {declarerNames[contract.declarer]}
      </div>
    </div>
  );
}

ContractBadge.propTypes = {
  contract: PropTypes.shape({
    level: PropTypes.number.isRequired,
    strain: PropTypes.oneOf(['S', 'H', 'D', 'C', 'NT']).isRequired,
    declarer: PropTypes.oneOf(['N', 'E', 'S', 'W']).isRequired,
    doubled: PropTypes.bool,
    redoubled: PropTypes.bool
  }).isRequired
};

/**
 * OpeningLead - Main flow component
 */
function OpeningLead({
  handData,
  onComplete,
  onClose,
  handIndex = 0,
  totalHands = 1
}) {
  // Use provided hand data or fall back to mock data
  const currentHand = handData || MOCK_HANDS[handIndex % MOCK_HANDS.length];

  // Flow state
  const [flowState, setFlowState] = useState(FLOW_STATES.PRESENT);
  const [selectedCardIndex, setSelectedCardIndex] = useState(-1);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [startTime] = useState(Date.now());

  // Get the leader's hand
  const leaderHand = currentHand.hands[currentHand.leader === 'W' ? 'west' : 'east'];
  const sortedHand = useMemo(() => sortCards(leaderHand), [leaderHand]);

  // Find indices for correct/incorrect highlighting
  const optimalCardIndex = useMemo(() => {
    if (!evaluationResult) return -1;
    return sortedHand.findIndex(card =>
      cardsEqual(card, evaluationResult.optimalCard)
    );
  }, [sortedHand, evaluationResult]);

  const incorrectCardIndex = useMemo(() => {
    if (!evaluationResult || evaluationResult.isCorrect) return -1;
    return sortedHand.findIndex(card =>
      cardsEqual(card, evaluationResult.selectedCard)
    );
  }, [sortedHand, evaluationResult]);

  // Compute disabled indices (all cards except selected after selection)
  const disabledIndices = useMemo(() => {
    if (flowState === FLOW_STATES.PRESENT) return [];
    // After selection, disable all cards
    return sortedHand.map((_, i) => i);
  }, [flowState, sortedHand]);

  /**
   * Handle card selection
   */
  const handleCardClick = useCallback((index) => {
    if (flowState !== FLOW_STATES.PRESENT) return;

    const selectedCard = sortedHand[index];
    setSelectedCardIndex(index);
    setFlowState(FLOW_STATES.SELECT);

    // Simulate evaluation delay (400ms as per spec)
    setTimeout(() => {
      const result = evaluateLead(selectedCard, currentHand);
      setEvaluationResult(result);
      setFlowState(FLOW_STATES.EVALUATE);

      // Transition to result after brief delay
      setTimeout(() => {
        setFlowState(FLOW_STATES.RESULT);
      }, 200);
    }, 400);
  }, [flowState, sortedHand, currentHand]);

  /**
   * Handle next hand / completion
   */
  const handleNext = useCallback(() => {
    const timeSpent = Date.now() - startTime;
    const flowResult = createFlowResult(currentHand, evaluationResult, timeSpent);

    if (onComplete) {
      onComplete(flowResult);
    }
  }, [currentHand, evaluationResult, startTime, onComplete]);

  // Get result message for display
  const resultMessage = evaluationResult ? getResultMessage(evaluationResult) : null;

  // Get comparison data for the table
  const comparisonData = useMemo(() => {
    if (!evaluationResult) return [];
    return getLeadComparison(
      currentHand.leadEvaluations,
      evaluationResult.selectedCard,
      evaluationResult.optimalCard
    );
  }, [currentHand.leadEvaluations, evaluationResult]);

  // Step indicator
  const stepIndicator = totalHands > 1
    ? `Hand ${handIndex + 1} of ${totalHands}`
    : undefined;

  /**
   * Render felt zone content
   */
  const renderFeltContent = () => (
    <div className="opening-lead-felt">
      {/* Contract Display */}
      <ContractBadge contract={currentHand.contract} />

      {/* Auction */}
      <div className="lead-auction-section">
        <div className="lead-auction-label">Auction</div>
        <BidTable
          bids={currentHand.auction}
          dealer={currentHand.auction[0]?.bidder || 'N'}
          playerSeat={currentHand.leader}
        />
      </div>

      {/* Leader's Hand */}
      <div className="lead-hand-section">
        <div className="lead-hand-label">
          Your Hand ({getLeaderName(currentHand.leader)})
        </div>
        <HandDisplay
          cards={sortedHand}
          mode="hand-h"
          selectable={flowState === FLOW_STATES.PRESENT}
          selectedIndex={selectedCardIndex}
          correctIndex={flowState === FLOW_STATES.RESULT ? optimalCardIndex : -1}
          incorrectIndex={flowState === FLOW_STATES.RESULT ? incorrectCardIndex : -1}
          disabledIndices={flowState !== FLOW_STATES.PRESENT ? disabledIndices : []}
          onCardClick={handleCardClick}
        />
      </div>
    </div>
  );

  /**
   * Render interaction zone content based on state
   */
  const renderInteractionContent = () => {
    switch (flowState) {
      case FLOW_STATES.PRESENT:
        return (
          <div className="opening-lead-interaction">
            <p className="lead-prompt">
              You are <span className="lead-prompt-highlight">{getLeaderName(currentHand.leader)}</span> on lead.
              <br />
              Pick your opening lead.
            </p>
          </div>
        );

      case FLOW_STATES.SELECT:
        return (
          <div className="opening-lead-interaction">
            <div className="lead-evaluating">
              <div className="lead-evaluating-spinner" />
              <span>Evaluating...</span>
            </div>
          </div>
        );

      case FLOW_STATES.EVALUATE:
      case FLOW_STATES.RESULT:
        return (
          <div className="opening-lead-interaction">
            <div className="lead-result-section">
              {/* Result Strip */}
              {resultMessage && (
                <ResultStrip
                  type={resultMessage.type}
                  message={resultMessage.message}
                  detail={resultMessage.detail}
                />
              )}

              {/* Explanation */}
              {flowState === FLOW_STATES.RESULT && evaluationResult && (
                <p className="lead-explanation">
                  {evaluationResult.explanation}
                </p>
              )}

              {/* Compare Table */}
              {flowState === FLOW_STATES.RESULT && comparisonData.length > 0 && (
                <div className="lead-compare-section">
                  <div className="lead-compare-title">Lead Comparison</div>
                  <LeadCompareTable
                    leads={comparisonData}
                    selectedCard={evaluationResult?.selectedCard}
                    optimalCard={evaluationResult?.optimalCard}
                  />
                </div>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  /**
   * Render action bar content
   */
  const renderActionContent = () => {
    if (flowState !== FLOW_STATES.RESULT) return null;

    return (
      <div className="lead-actions">
        <PrimaryButton onClick={handleNext}>
          {handIndex < totalHands - 1 ? 'Next Hand' : 'Complete'}
        </PrimaryButton>
      </div>
    );
  };

  return (
    <FlowLayout
      title="Opening Lead Quiz"
      stepIndicator={stepIndicator}
      onClose={onClose}
      feltContent={renderFeltContent()}
      interactionContent={renderInteractionContent()}
      actionContent={renderActionContent()}
    />
  );
}

OpeningLead.propTypes = {
  /**
   * Hand data to use. If not provided, uses mock data.
   */
  handData: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string,
    description: PropTypes.string,
    leader: PropTypes.oneOf(['W', 'E']).isRequired,
    contract: PropTypes.object.isRequired,
    auction: PropTypes.array.isRequired,
    hands: PropTypes.object.isRequired,
    leadEvaluations: PropTypes.array.isRequired,
    optimalLead: PropTypes.object.isRequired,
    explanation: PropTypes.string.isRequired
  }),

  /**
   * Callback when the flow is completed
   * @param {Object} flowResult - The FlowResult object
   */
  onComplete: PropTypes.func,

  /**
   * Callback when close button is clicked
   */
  onClose: PropTypes.func,

  /**
   * Current hand index (0-based) for multi-hand sessions
   */
  handIndex: PropTypes.number,

  /**
   * Total number of hands in the session
   */
  totalHands: PropTypes.number
};

export default OpeningLead;
