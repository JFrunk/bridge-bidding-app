import React from 'react';
import './PlayWorkspace.css';

/**
 * PlayWorkspace - Container for card play practice
 *
 * Options:
 * - New Hand: AI bids all hands, user plays
 * - Play Last Bid Hand: Play the hand just finished bidding
 * - Replay Last Played: Replay the most recent played hand
 */
export function PlayWorkspace({
  onNewHand,
  onPlayLastBid,
  onReplayLast,
  hasLastBidHand,
  hasLastPlayedHand,
  isPlaying,
  children  // The actual play UI passed from App.js
}) {
  // If already playing, just show the play UI
  if (isPlaying) {
    return (
      <div className="play-workspace playing">
        {children}
      </div>
    );
  }

  // Show play options
  return (
    <div className="play-workspace">
      <div className="play-options-container">
        <div className="play-header">
          <h2>Card Play Practice</h2>
          <p>Choose how you want to practice card play</p>
        </div>

        <div className="play-options-grid">
          {/* New Hand Option */}
          <div className="play-option-card">
            <div className="option-icon">🎲</div>
            <h3>New Hand</h3>
            <p>
              AI bids all four hands automatically.
              Focus purely on card play as declarer or defender.
            </p>
            <button
              className="option-button primary"
              onClick={onNewHand}
              data-testid="play-new-hand"
            >
              Deal & Play
            </button>
          </div>

          {/* Play Last Bid Hand */}
          <div className={`play-option-card ${!hasLastBidHand ? 'disabled' : ''}`}>
            <div className="option-icon">📝</div>
            <h3>Play Last Bid Hand</h3>
            <p>
              Continue to card play with the hand you just finished bidding.
            </p>
            <button
              className="option-button secondary"
              onClick={onPlayLastBid}
              disabled={!hasLastBidHand}
              data-testid="play-last-bid"
            >
              {hasLastBidHand ? 'Play This Hand' : 'No Hand Available'}
            </button>
          </div>

          {/* Replay Last Played Hand */}
          <div className={`play-option-card ${!hasLastPlayedHand ? 'disabled' : ''}`}>
            <div className="option-icon">🔄</div>
            <h3>Replay Last Hand</h3>
            <p>
              Play through the same hand again to try different strategies.
            </p>
            <button
              className="option-button secondary"
              onClick={onReplayLast}
              disabled={!hasLastPlayedHand}
              data-testid="play-replay"
            >
              {hasLastPlayedHand ? 'Replay Hand' : 'No Hand Available'}
            </button>
          </div>
        </div>

        <div className="play-tips">
          <h4>Tips</h4>
          <ul>
            <li>As declarer, plan your play before playing from dummy</li>
            <li>Count your winners and losers</li>
            <li>Watch for opponent signals when defending</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default PlayWorkspace;
